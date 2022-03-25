# Objetivo
Esse projeto foi criado para facilitar o uso dos dados originários do Nubank em um ambiente Django.
A principal característica é registrar `models` que irão colocar os dados da sua conta Nubank em tabelas (modelos `CardStatement` e `AccountStatement`)
de forma que sejá fácil trabalhar com esses dados. Isso facilita alguns casos de uso como acompanhamento de gastos para fins de orçamento etc.

# Setup (dev)
TODO: disponibilizar via pip
Atualmente, para uma instalação editável:
`pip install -e .`

Esse projeto considera que existem 3 variáveis de ambiente no contexto:
`NUBANK_CPF`, `NUBANK_PASSWORD` e `NUBANK_CERT_PATH`
Os 2 primeiros são autoexplicativos, já o último é o certificado gerado a partir do processo de autenticação explicado no readme do pynubank.

Adicione `nubank_django` como na sua lista de `INSTALLED_APPS` no `settings.py` do seu projeto Django para começar a usar.
```
INSTALLED_APPS = [
    "django.contrib.admin",
    ...
    "nubank_django",
]
```

Execute `python manage.py migrate` para criação das tabelas no banco de dados.
Esse projeto inclui classes para `admin` do Django já registradas, que irão aparecer no seu projeto.
Caso deseje removê-las, basta colocar executar em seu projeto, por exemplo:
`admin.site.unregister(CardStatement)`

# Fluxo dos dados
```mermaid
flowchart LR

nubank_api --> pynubank --> nubank_django
```
