# ControleEntregaSB

Aplicação Django para controle de entregas do Super Baranda.

Interface adaptada para a identidade visual da empresa, usando azul, vermelho, verde e turquesa da marca. A integração com PDV não faz parte do escopo.

## Fluxo de uso

1. O usuário entra no sistema com login e senha.
2. A equipe lança a entrega em **Lançamento**.
3. O sistema gera automaticamente o número de controle do dia.
4. A entrega entra como **Pendente** com data prevista.
5. A expedição acessa **Rotas > Montar rota**.
6. Seleciona entregas pendentes, informa motorista e responsável pela saída.
7. O sistema cria uma rota/romaneio e marca as entregas como **Em rota**.
8. A rota pode ser impressa em formato de romaneio.
9. No retorno, a equipe registra entrega, cancelamento ou reagendamento.
10. O sistema grava histórico de eventos e comprovante simples.
11. Quando todas as entregas da rota são fechadas, a rota fica **Finalizada**.

## Funcionalidades

- Login e logout
- Dashboard diário
- Lançamento de entregas
- Número de controle diário automático
- Cadastro de motoristas
- Cadastro de operadores
- Cadastro de motivos de insucesso
- Montagem de rota/romaneio
- Impressão de romaneio
- Fechamento em lote de rota
- Motivos de cancelamento/insucesso
- Reagendamento de entrega
- Comprovante simples: recebedor, documento e observação
- Histórico de eventos da entrega
- Relatório com filtros
- Exportação CSV
- Administração Django

## Como executar

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse: http://127.0.0.1:8000/

## Testes

```bash
python manage.py test
```
