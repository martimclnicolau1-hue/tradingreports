# -*- coding: utf-8 -*-
"""Monte Carlo EDUCATIVO + sanity-backtest walk-forward.

AVISO IMPORTANTE: o Monte Carlo simula uma estratégia GENÉRICA parametrizada
por ti — não é uma recomendação sobre o teu dinheiro. As probabilidades de
cenário são inputs teus; o simulador só mostra as consequências matemáticas
das TUAS hipóteses (garbage in, garbage out).
"""
import numpy as np


def walk_forward_check(all_reactions_by_ticker, min_n=8, skew_cut=0.25):
    """Sanity-backtest da regra de seleção 'skew positivo' SEM lookahead:
    para cada ticker, usa os primeiros k trimestres para calcular o skew e
    verifica o retorno do trimestre k+1. Repete rolando. Devolve o retorno
    médio das seleções vs. não-seleções — se a diferença for ~0, a regra
    não tem edge histórico e o relatório di-lo abertamente.
    """
    sel_rets, rej_rets = [], []
    for _tkr, reactions in all_reactions_by_ticker.items():
        rs = [r["reaction"] for r in reversed(reactions)]  # cronológico
        for k in range(min_n, len(rs)):
            past = np.array(rs[:k])
            skew = (past >= 0.10).mean() - (past <= -0.10).mean()
            nxt = rs[k]
            (sel_rets if skew >= skew_cut else rej_rets).append(nxt)
    def s(a):
        if not a:
            return {"n": 0}
        a = np.array(a)
        return {"n": len(a), "mean_ret": float(a.mean()), "median": float(np.median(a)),
                "hit_rate_pos": float((a > 0).mean())}
    out = {"selecionados": s(sel_rets), "rejeitados": s(rej_rets)}
    # haircut de comparações múltiplas: com ~T tickers testados, exige-se que
    # a diferença de médias exceda 2 erros-padrão combinados para ser citada
    if sel_rets and rej_rets:
        a, b = np.array(sel_rets), np.array(rej_rets)
        se = np.sqrt(a.var() / len(a) + b.var() / len(b))
        diff = a.mean() - b.mean()
        out["diff_mean"] = float(diff)
        out["passes_2se"] = bool(abs(diff) > 2 * se)
        out["conclusao"] = ("Edge histórico estatisticamente distinguível" if abs(diff) > 2 * se
                            else "SEM edge distinguível de ruído — trata o skew como tie-breaker, não sinal")
    return out
