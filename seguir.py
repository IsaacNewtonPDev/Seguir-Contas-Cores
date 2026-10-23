"""
seguir.py - Segue contas do Instagram listadas em uma planilha, filtrando por
orientação (esquerda, direita ou balanceado), com limite diário e pausas
aleatórias entre as ações.

Uso:
    python seguir.py --orientacao balanceado --n 20 --limite-dia 10
"""
import argparse
import random
import time
from datetime import date
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

# ---- Configurações padrão (podem ser sobrescritas por argumentos) ----------
PLANILHA = "perfis.xlsx"
COL_ARROBA = "Usuário"
COL_ORIENTACAO = "Orientação"
PERFIL_SESSAO = "sessao_conta"   # pasta onde o login fica salvo (uma por conta)
LOG = "seguidos.csv"             # registro: arroba,data
PAUSA_MIN, PAUSA_MAX = 45, 120   # segundos entre um follow e outro
# -----------------------------------------------------------------------------


def ler_log(caminho: Path):
    """Retorna (conjunto de arrobas já seguidos, quantos foram seguidos hoje)."""
    if not caminho.exists():
        return set(), 0
    seguidos, hoje = set(), 0
    for linha in caminho.read_text().splitlines():
        if not linha.strip():
            continue
        arroba, data = linha.split(",")
        seguidos.add(arroba)
        if data == str(date.today()):
            hoje += 1
    return seguidos, hoje


def selecionar(df, orientacao, n, col_arroba, col_orientacao):
    """Monta a lista de arrobas a seguir, de acordo com a orientação pedida."""
    df = df.copy()
    df[col_orientacao] = df[col_orientacao].astype(str).str.strip().str.lower()
    df[col_arroba] = df[col_arroba].astype(str).str.strip().str.lstrip("@")

    if orientacao in ("esquerda", "direita"):
        return df[df[col_orientacao] == orientacao][col_arroba].tolist()

    # balanceado: n de cada lado, sorteio fixo (mesma lista em todos os dias)
    esq = df[df[col_orientacao] == "esquerda"][col_arroba]
    dir_ = df[df[col_orientacao] == "direita"][col_arroba]
    k = min(n, len(esq), len(dir_))
    if k < n:
        print(f"[!] Só há {k} perfis de um dos lados; usando n={k}.")
    esq = esq.sample(k, random_state=42).tolist()
    dir_ = dir_.sample(k, random_state=42).tolist()
    # intercala esquerda/direita para manter o equilíbrio ao longo dos dias
    return [x for par in zip(esq, dir_) for x in par]


def seguir(page, arroba):
    """Abre o perfil e clica em 'Seguir'. Retorna True se seguiu."""
    page.goto(f"https://www.instagram.com/{arroba}/", wait_until="domcontentloaded")
    page.wait_for_timeout(random.randint(2000, 4000))

    botao = page.get_by_role("button", name="Seguir", exact=True)
    if botao.count() == 0:
        print(f"[-] {arroba}: sem botão 'Seguir' (já segue, não existe ou pendente)")
        return False

    botao.first.click()
    page.wait_for_timeout(1500)
    print(f"[+] seguiu {arroba}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Segue perfis do Instagram a partir de uma planilha.")
    ap.add_argument("--orientacao", choices=["esquerda", "direita", "balanceado"], required=True)
    ap.add_argument("--n", type=int, default=20, help="qtd de cada lado no modo balanceado (padrão: 20)")
    ap.add_argument("--limite-dia", type=int, default=25, help="máximo de follows por dia (padrão: 25)")
    ap.add_argument("--planilha", default=PLANILHA, help=f"arquivo .xlsx (padrão: {PLANILHA})")
    ap.add_argument("--col-arroba", default=COL_ARROBA, help=f"coluna dos usuários (padrão: {COL_ARROBA})")
    ap.add_argument("--col-orientacao", default=COL_ORIENTACAO, help=f"coluna da orientação (padrão: {COL_ORIENTACAO})")
    ap.add_argument("--sessao", default=PERFIL_SESSAO, help="pasta do perfil do navegador (uma por conta)")
    ap.add_argument("--log", default=LOG, help="arquivo de registro dos follows")
    args = ap.parse_args()

    log = Path(args.log)
    seguidos, hoje = ler_log(log)
    restante = args.limite_dia - hoje
    if restante <= 0:
        print(f"Limite diário ({args.limite_dia}) já atingido. Volte amanhã.")
        return

    df = pd.read_excel(args.planilha)
    lista = selecionar(df, args.orientacao, args.n, args.col_arroba, args.col_orientacao)
    alvos = [a for a in lista if a not in seguidos][:restante]
    print(f"{len(alvos)} perfis nesta rodada (já seguiu {hoje} hoje)")
    if not alvos:
        print("Nada a fazer: todos os perfis da lista já foram seguidos.")
        return

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(args.sessao, headless=False)
        page = ctx.new_page()
        page.goto("https://www.instagram.com/")
        input("Confira se está logado na conta certa (faça login se precisar) e aperte ENTER...")

        for arroba in alvos:
            try:
                if seguir(page, arroba):
                    with log.open("a") as f:
                        f.write(f"{arroba},{date.today()}\n")
            except Exception as e:
                print(f"[!] erro em {arroba}: {e}")
            time.sleep(random.randint(PAUSA_MIN, PAUSA_MAX))

        ctx.close()


if __name__ == "__main__":
    main()
