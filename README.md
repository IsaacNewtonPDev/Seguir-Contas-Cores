# seguir-insta-cores

Script em Python que lê uma planilha de perfis do Instagram e segue as contas
automaticamente, filtrando por **orientação** (`esquerda`, `direita` ou
`balanceado`). Foi feito para apoiar um projeto de extensão que audita o
algoritmo de recomendação de redes sociais usando contas artificiais
(*sock puppets*).

O script usa o [Playwright](https://playwright.dev/python/) para controlar um
navegador Chromium, com **limite diário** e **pausas aleatórias** entre as
ações para reduzir o risco de bloqueio da conta.

> ⚠️ **Aviso.** Automatizar ações no Instagram viola os Termos de Uso da Meta e
> as contas usadas podem ser limitadas ou banidas. Use apenas com contas
> criadas para a pesquisa e de acordo com as orientações da coordenação do
> projeto (incluindo questões éticas e de pesquisa). Este repositório não tem
> nenhuma ligação com a Meta.

## Como funciona

- Lê a planilha `.xlsx` com os usuários e a orientação de cada um.
- Seleciona os perfis conforme o modo escolhido.
- Abre cada perfil no Instagram e clica em **Seguir**.
- Registra cada follow em `seguidos.csv` (arroba + data), então nunca segue a
  mesma conta duas vezes e retoma de onde parou no dia seguinte.
- Respeita um limite de follows **por dia**, somando todas as execuções do dia.
- O login fica salvo na pasta `sessao_conta/`, então só é preciso entrar na
  conta uma vez.

## Modos

| Modo | O que faz |
|---|---|
| `esquerda` | Segue só os perfis marcados como esquerda |
| `direita` | Segue só os perfis marcados como direita |
| `balanceado` | Segue `n` de esquerda e `n` de direita, **intercalados** (esq, dir, esq, dir...), então qualquer limite par mantém o equilíbrio 50/50 |

No modo balanceado o sorteio usa uma semente fixa, então a lista é sempre a
mesma entre os dias.

## Requisitos

- Python 3.9+
- Linux, macOS ou Windows

## Instalação

```bash
git clone <URL-DO-REPOSITORIO>
cd seguir-insta-cores

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium
```

Em Ubuntu/Debian, se faltar o `venv` ou alguma dependência do navegador:

```bash
sudo apt install python3-venv -y
playwright install-deps chromium
```

## Planilha

Coloque na pasta do projeto um arquivo `perfis.xlsx` com, no mínimo, estas
colunas (a coluna de partido, se existir, é ignorada):

| Usuário | Partido | Orientação |
|---|---|---|
| @exemplo_um | XXX | direita |
| @exemplo_dois | YYY | esquerda |

- O `@` é opcional, o script remove sozinho.
- Os valores de orientação devem ser `esquerda` ou `direita` (maiúsculas e
  minúsculas não importam).
- Se os nomes das colunas ou do arquivo forem outros, use `--planilha`,
  `--col-arroba` e `--col-orientacao` (veja abaixo).

> A planilha `perfis.xlsx` já vem no repositório. Se ela for atualizada, baixe
> a versão nova (ou rode `git pull`).

## Uso

Sempre com o ambiente virtual ativado, dentro da pasta do projeto:

```bash
# teste pequeno
python seguir.py --orientacao balanceado --n 20 --limite-dia 3

# rotina normal
python seguir.py --orientacao esquerda
python seguir.py --orientacao direita
python seguir.py --orientacao balanceado --n 20 --limite-dia 10
```

Na primeira execução abre uma janela do navegador. **Faça login na conta do
bot, volte ao terminal e aperte ENTER.** A partir daí o script trabalha sozinho
e fecha o navegador no final. Não é necessário (nem recomendado) sair da conta
depois: o login fica salvo para os próximos dias.

### Opções

| Opção | Padrão | Descrição |
|---|---|---|
| `--orientacao` | (obrigatório) | `esquerda`, `direita` ou `balanceado` |
| `--n` | `20` | No balanceado, quantos perfis de cada lado |
| `--limite-dia` | `25` | Máximo de follows por dia (somando todas as execuções) |
| `--planilha` | `perfis.xlsx` | Caminho da planilha |
| `--col-arroba` | `Usuário` | Nome da coluna dos usuários |
| `--col-orientacao` | `Orientação` | Nome da coluna da orientação |
| `--sessao` | `sessao_conta` | Pasta do perfil do navegador (use uma por conta) |
| `--log` | `seguidos.csv` | Arquivo de registro dos follows |

## Várias contas

Cada conta bot precisa da **sua própria** pasta de sessão e do **seu próprio**
log, senão os logins e os registros se misturam:

```bash
python seguir.py --orientacao esquerda --sessao sessao_esq --log seguidos_esq.csv
python seguir.py --orientacao direita  --sessao sessao_dir --log seguidos_dir.csv
```

## Evitando bloqueios

Não existe um número oficial, mas na prática:

| Idade da conta | Sugestão de `--limite-dia` |
|---|---|
| Dias 1 a 3 | 5 a 10 |
| Dias 4 a 7 | 15 |
| Depois | 20 a 25 |

Outras dicas:

- Use a conta de forma normal nos primeiros dias (entrar, rolar o feed) antes
  de rodar o script.
- Divida o dia em 2 ou 3 rodadas, com algumas horas de intervalo, em vez de
  seguir tudo de uma vez.
- Se aparecer qualquer aviso do Instagram ("atividade suspeita", pedido de
  confirmação), pare com `Ctrl + C` e espere 1 ou 2 dias.
- Não rode este script ao mesmo tempo que outro script usando a mesma conta ou
  a mesma pasta de sessão.
- Para ritmo mais lento, aumente `PAUSA_MIN` e `PAUSA_MAX` no topo do
  `seguir.py`.

## Problemas comuns

| Erro | Solução |
|---|---|
| `No module named ...` | Ative o venv e rode `pip install -r requirements.txt` |
| `Executable doesn't exist` | Rode `playwright install chromium` |
| `KeyError: 'Usuário'` | O nome da coluna não bate; use `--col-arroba` / `--col-orientacao` |
| `sem botão 'Seguir'` em todos | A conta está em inglês (troque `"Seguir"` por `"Follow"` no script) ou o Instagram mudou a interface |
| Erro de perfil já em uso | Outro Chromium está usando a mesma `--sessao`; feche-o |

## Limitações

- O Instagram muda a interface com frequência; o script procura o botão pelo
  texto "Seguir" e pode precisar de ajustes.
- Só funciona com a interface do Instagram em português.
- Não faz coleta de dados, apenas segue as contas.
