while True:
    import re
    import time
    import telebot
    from pandas import read_sql_query, DataFrame
    from sqlalchemy import create_engine, text
    from datetime import datetime

    token = 'token'
    bot = telebot.TeleBot(token)

    print('Bot James em operação...')

    # Define connection and file paths
    ORACLE_CONN_STRING = 'oracle+cx_oracle://USER_ID:PSW@HOST/DB'

    dia = datetime.strptime(datetime.now().date().strftime('%d/%m/%Y'), '%d/%m/%Y').date()
    precoprom = ''


    def create_price(codigoproduto, preco, cliente, fifo):
        global precoprom

        # Select information from database
        codred = ('select '
                  ' codcli '
                  ',codrede '

                  'from '
                  'pcclient '

                  'where '
                  '    codrede not in (14, 26, 32, 34, 59) '
                  'and codrede is not null '

                  'order by '
                  'codcli ')

        prodprinc = ('select '
                     'codprodprinc '

                     'from '
                     'pcprodut '

                     'where '
                     'codprod = :codprod ')

        codprecoprom = 'SELECT DFSEQ_PCPRECOPROM.NEXTVAL FROM DUAL'

        filial_regiao = ('select '
                         '  i.codcli '
                         ', i.codfilialnf '
                         ', i.numregiao '
                         ', c.tipofj '

                         'from '
                         '  pctabprcli i '
                         ', pcclient c '

                         'where '
                         '    c.codcli = i.codcli '
                         'and c.codusur1 <> 999 '
                         'and i.numregiao in (1,5,7,12) '
                         'and i.codfilialnf <> 2 '

                         'order by '
                         'codcli ')
        params = {"codprod": codigoproduto}

        # Create dataframes from database
        with create_engine(ORACLE_CONN_STRING).begin() as conn:
            df_rede = DataFrame(read_sql_query(sql=text(codred), con=conn))
        with create_engine(ORACLE_CONN_STRING).begin() as conn:
            df_regiao_filial = DataFrame(read_sql_query(sql=text(filial_regiao), con=conn))
        with create_engine(ORACLE_CONN_STRING).begin() as conn:
            prodprincipal = DataFrame(read_sql_query(sql=text(prodprinc), con=conn, params=params)).iloc[0, 0]
        with create_engine(ORACLE_CONN_STRING).begin() as conn:
            precoprom = DataFrame(read_sql_query(sql=text(codprecoprom), con=conn)).iloc[0, 0] + 1

        # Select regiao and filial
        if not df_regiao_filial.loc[(df_regiao_filial['codcli'] == cliente) & (df_regiao_filial['tipofj'] == 'J')] \
                .empty:
            filial = str((df_regiao_filial.loc[df_regiao_filial['codcli'] == cliente, ['codfilialnf']]).iloc[0, 0])
            regiao = (df_regiao_filial.loc[df_regiao_filial['codcli'] == cliente, ['numregiao']]).iloc[0, 0]
        else:
            filial = str(4)
            regiao = 7

        # Select cod_cli or cod_rede
        if not df_rede.loc[df_rede['codcli'] == cliente].empty:
            rede = (df_rede.loc[df_rede['codcli'] == cliente, ['codrede']]).iloc[0, 0]
            cliente = 0
        else:
            rede = 0

        if fifo:
            filial = 2

        # Make dataframe with values to discount campaign
        sql = DataFrame([{'codprecoprom': precoprom, 'codprod': prodprincipal, 'codfilial': filial, 'numregiao': regiao,
                          'precofixo': preco, 'codcli': cliente, 'codrede': rede, 'codfuncultalter': 1,
                          'agregarst': 'N', 'utilizaprecofixofamilia': 'S', 'enviafv': 'S', 'dtiniciovigencia': dia,
                          'dtfimvigencia': dia, 'dtultalter': dia, 'consideracalcgiro': 'N', 'syncfv': 'S',
                          'prioritaria': 'S', 'origemped': 'O', 'validotodasembalagens': 'S',
                          'consideraprecosemimposto': 'N', 'consideracalcgiromedic': 'N'}])

        # Create price discount campaign on database
        with create_engine(ORACLE_CONN_STRING).begin():
            sql.to_sql('pcprecoprom', create_engine(ORACLE_CONN_STRING), if_exists='append', index=False)

        # Execute statement of updates
        if cliente == 0:
            update_statement = 'update pcprecoprom set codcli = null where codcli = 0'
            with create_engine(ORACLE_CONN_STRING).begin() as conn:
                conn.execute(text(update_statement))
        if rede == 0:
            update_statement = 'update pcprecoprom set codrede = null where codrede = 0'
            with create_engine(ORACLE_CONN_STRING).begin() as conn:
                conn.execute(text(update_statement))

    @bot.message_handler(func=lambda message: True)  # Connect and answer Telegram
    def handle_message(message):
        global precoprom
        codigoproduto = ''
        fifo = False
        # Verify if the message is a reply and if it has 'ok' as a message
        if message.reply_to_message is not None and message.text.lower() == 'ok' and \
                message.from_user.username == 'Manager':
            time.sleep(2)
            try:
                # Verify if there is all information required
                if 'cliente' in message.reply_to_message.text.lower() and 'produto' in \
                        message.reply_to_message.text.lower() and 'preço' or 'preco' in \
                        message.reply_to_message.text.lower():
                    lines = message.reply_to_message.text.lower().split('\n')
                    cliente = ''
                    codigos_precos = []
                    # Separate in blocks to validate each message
                    for line in lines:
                        if 'fifo' in line.lower():
                            fifo = True
                        if 'cliente' in line.lower():
                            cliente = int((re.findall(r'\d+', line)[0]).strip())
                        if 'descr' in line.lower():
                            continue
                        if 'produto' in line.lower():
                            codigoproduto = int((re.findall(r'\d+', line)[0]).strip())
                            codigos_precos.append((codigoproduto, None))
                        elif 'preço' or 'preco' in line.lower():
                            if 'preço' in line.lower():
                                if codigoproduto is not None and codigos_precos[-1][1] is None:
                                    preco = float((re.findall(r'\d+[,.]?\d*', line.replace(',', '.'))[0]).strip())
                                    codigos_precos[-1] = (codigos_precos[-1][0], preco)
                            elif 'preco' in line.lower():
                                preco = float((re.findall(r'\d+[,.]?\d*', line.replace(',', '.'))[0]).strip())
                                codigos_precos[-1] = (codigos_precos[-1][0], preco)

                    # Execute function to save all information in database
                    for codigo, preco in codigos_precos:
                        if preco is not None:
                            create_price(codigo, preco, cliente, fifo)
                            bot.reply_to(message, 'Preço criado com sucesso!')
                            bot.send_message(message.chat.id, f'Precificação Nº: {precoprom}\n'
                                                              f'Cliente: {cliente}\nProduto: {codigo}\nPreço: {preco}')
                    time.sleep(1)
            except telebot.apihelper.ApiTelegramException as e:
                # Handle API exception
                if e.error_code == 429:
                    error_message = (f"Erro {e.error_code}: {e.description} \nManager, muitas aprovações"
                                     f"foram realizadas em um curto período de tempo, autorize pausadamente "
                                     f"durante os próximos minutos")
                    bot.send_message(message.chat.id, error_message)
                else:
                    error_message = f"Erro {e.error_code}: {e.description}"
                    bot.send_message(message.chat.id, error_message)
                time.sleep(30)

            except IndexError:
                bot.reply_to(message, 'ERRO AO PROCESSAR. Palavra desconhecida presente ou cliente, produto '
                                      'inexistente. Favor enviar a solicitação como no modelo fixado.')
            except ValueError:
                bot.reply_to(message, 'ERRO AO PROCESSAR. Valor inválido enviado.')
            except ConnectionError:
                bot.reply_to(message, 'ERRO AO PROCESSAR. Falha de conexão.')
            except TimeoutError:
                bot.reply_to(message, 'ERRO AO PROCESSAR. Tempo ou número máximo de tentativas alcançados.')
            except Exception:
                bot.reply_to(message, 'ERRO AO PROCESSAR. Erro desconhecido.')


    bot.infinity_polling()
    print('Encerrado')
