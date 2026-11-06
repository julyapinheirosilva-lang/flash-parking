# Flash Parking — Projeto de estacionamento

## Requisitos
- Python 3.10 ou superior
- Visual Studio Code
- Internet para carregar Bootstrap, ícones e fontes (o sistema funciona sem eles, mas fica sem parte do visual)

## Como executar no Windows
1. Extraia `estacionamento_flash.zip`.
2. Abra a pasta `estacionamento_flash` no VS Code.
3. Abra o terminal do VS Code: Terminal > Novo Terminal.
4. Crie um ambiente virtual (recomendado):
   `py -m venv .venv`
5. Ative:
   PowerShell: `.venv\Scripts\Activate.ps1`
   Se o PowerShell bloquear, use o Prompt de Comando e execute: `.venv\Scripts\activate.bat`
6. Instale as dependências:
   `py -m pip install -r requirements.txt`
7. Inicie:
   `py app.py`
8. Abra no navegador:
   `http://127.0.0.1:5000`

O arquivo `estacionamento.db` é criado automaticamente na primeira execução. Não apague esse arquivo se quiser manter os cadastros.

## Primeiro uso
1. Cadastre um cliente.
2. Cadastre um veículo com a placa e associe ao cliente.
3. Entre em Vagas para conferir as 20 vagas iniciais ou adicionar outras.
4. Em Entradas e saídas, informe a placa e escolha uma vaga livre.
5. Para encerrar a estadia, escolha a forma de pagamento e clique em Registrar saída.
6. Ajuste a tarifa por hora em Tabela de preços.

## O que está implementado
- Dashboard com contadores e faturamento do dia.
- Cadastro de clientes e veículos.
- Vagas normais, preferenciais, idosos, PCD, motos e elétricas.
- Controle de entrada/saída por placa e bloqueio de vaga ocupada.
- Cálculo de cobrança por hora iniciada.
- Registro de pagamento em dinheiro, cartão ou PIX.
- Configuração de tarifas hora, diária, mensal e anual.
- Relatórios de pagamentos e uso das categorias.
- Persistência em SQLite.

## Observações para apresentação
- A cobrança automática de saída usa a tarifa por hora. As tarifas diária, mensal e anual ficam configuráveis e cadastradas, mas a lógica de planos recorrentes pode ser desenvolvida como próxima etapa.
- Este é um projeto acadêmico local. Antes de uso comercial, adicione autenticação, permissões, validações adicionais, cópias de segurança e proteção de dados.
