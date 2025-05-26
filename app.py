import pymysql
import uuid

conexao = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database=''
)
cursor = conexao.cursor()

while True:
    print("\nMenu:")
    print("A) Visitante")
    print("B) Colaborador")
    print("C) Registrar em evento")
    print("D) Lista de presença (por ID do crachá)")
    print("E) Dar presença (por ID do crachá)")
    print("S) Sair")

    resposta = input("Escolha a opção: ").strip().upper()

    if resposta in ("A", "B"):
        nome = input("Nome: ")
        data_nasc = input("Data de nascimento (AAAA-MM-DD): ")
        numero = input("Número de telefone: ")
        cpf = input("CPF (apenas números): ").strip()
        email = input("E-mail: ").strip()

        if len(cpf) != 11:
            print("CPF inválido: deve conter exatamente 11 dígitos numéricos.")
            continue
        elif cpf == cpf[0] * 11:
            print("CPF inválido: não pode ser uma sequência repetitiva de números.")
            continue

        if "@" not in email or "." not in email.split("@")[-1]:
            print("E-mail inválido.")
            continue

        colaborador = 1 if resposta == "B" else 0
        cart_trabalho = input(
            "Carteira de trabalho: ") if colaborador else None
        cep = input("CEP: ") if colaborador else None

        try:
            cursor.execute("""
                INSERT INTO lista_de_cadastrados 
                (cpf, nome, data_nasc, num_tel, email, colaborador, cart_trabalho, cep)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (cpf, nome, data_nasc, numero, email, colaborador, cart_trabalho, cep))
            conexao.commit()
            print("Cadastro realizado com sucesso!")
        except pymysql.Error as err:
            print(f"Erro ao cadastrar: {err}")
            continue

        registrar = input(
            'Deseja se registrar em um evento? (S/N): ').strip().upper()
        if registrar == 'S':
            cursor.execute("SELECT id_evento, nome_evento FROM eventos")
            eventos = cursor.fetchall()
            print("\nEventos disponíveis:")
            for id_evento, nome_evento in eventos:
                print(f"{id_evento} - {nome_evento}")

            id_evento = input("Digite o ID do evento: ").strip()
            id_cracha = (cpf[-2:] + id_evento.zfill(3))[:5]

            try:
                cursor.execute("""
                    INSERT INTO cracha (id_cracha, id_evento, cpf)
                    VALUES (%s, %s, %s)
                """, (id_cracha, int(id_evento), cpf))
                conexao.commit()
                print(f"Registrado com crachá: {id_cracha}")
            except pymysql.IntegrityError:
                print("Você já está registrado nesse evento.")
            except pymysql.Error as err:
                print(f"Erro ao registrar no evento: {err}")

    elif resposta == "C":
        cpf = input("Digite o CPF da pessoa: ").strip()
        cursor.execute(
            "SELECT cpf FROM lista_de_cadastrados WHERE cpf = %s", (cpf,))
        if cursor.fetchone():
            cursor.execute("SELECT id_evento, nome_evento FROM eventos")
            eventos = cursor.fetchall()
            print("\nEventos disponíveis:")
            for id_evento, nome_evento in eventos:
                print(f"{id_evento} - {nome_evento}")

            id_evento = input(
                "Digite o ID do evento para se registrar: ").strip()

            cursor.execute("""
                SELECT 1 FROM cracha
                WHERE cpf = %s AND id_evento = %s
                LIMIT 1
            """, (cpf, int(id_evento)))
            if cursor.fetchone():
                print("Você já está registrado neste evento.")
            else:
                id_cracha = (cpf[-2:] + str(uuid.uuid4().int)[:3])[:5]
                try:
                    cursor.execute("""
                        INSERT INTO cracha (id_cracha, id_evento, cpf)
                        VALUES (%s, %s, %s)
                    """, (id_cracha, int(id_evento), cpf))
                    conexao.commit()
                    print(f"Registrado com crachá: {id_cracha}")
                except pymysql.Error as err:
                    print(f"Erro ao registrar no evento: {err}")
        else:
            print("Pessoa não cadastrada.")

    elif resposta == "D":
        id_cracha = input("Digite o ID do crachá: ").strip()

        cursor.execute("""
            SELECT 
                e.nome_evento,
                COALESCE(lp.presenca, FALSE) AS presenca
            FROM 
                cracha c
            JOIN 
                eventos e ON c.id_evento = e.id_evento
            LEFT JOIN 
                lista_presenca lp ON c.id_cracha = lp.id_cracha
            WHERE 
                c.id_cracha = %s
        """, (id_cracha,))
        resultado = cursor.fetchone()

        if resultado:
            nome_evento, presenca = resultado
            status = 'Presente' if presenca else 'Ausente'
            print(f"\nPresença para o ID do crachá {id_cracha}:")
            print(f"- Evento: {nome_evento} | Presença: {status}")
        else:
            print("Nenhum dado encontrado para esse ID de crachá.")

    elif resposta == "E":
        id_cracha = input("Digite o ID do crachá para dar presença: ").strip()

        try:
            cursor.execute(
                "SELECT 1 FROM lista_presenca WHERE id_cracha = %s", (id_cracha,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE lista_presenca SET presenca = TRUE WHERE id_cracha = %s
                """, (id_cracha,))
            else:
                cursor.execute("""
                    INSERT INTO lista_presenca (id_cracha, presenca)
                    VALUES (%s, TRUE)
                """, (id_cracha,))
            conexao.commit()
            print("Presença registrada com sucesso.")
        except pymysql.Error as err:
            print(f"Erro ao registrar presença: {err}")

    elif resposta == "S":
        print("Saindo...")
        break

    else:
        print("Opção inválida.")

cursor.close()
conexao.close()
