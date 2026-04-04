"""
🎁 Sorteio de Amigo Secreto
============================
Uso:
    python amigo_secreto.py participantes.csv

O CSV deve ter as colunas: nome, email, preferencias

Configuração do Gmail (mestre da cerimônia):
    - Defina as variáveis de ambiente antes de rodar:
        export GMAIL_REMETENTE="seuemail@gmail.com"
        export GMAIL_SENHA_APP="sua_senha_de_app"

    - A senha de app é gerada em:
        https://myaccount.google.com/apppasswords
      (requer 2FA ativo na conta Google)
"""

import csv
import random
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ─────────────────────────────────────────────
#  CONFIGURAÇÕES — edite aqui se preferir
# ─────────────────────────────────────────────

GMAIL_REMETENTE = os.environ.get("GMAIL_REMETENTE", "seuemail@gmail.com")
GMAIL_SENHA_APP = os.environ.get("GMAIL_SENHA_APP", "sua_senha_de_app_aqui")

ASSUNTO_EMAIL = "🍫 Seu Amigo de Chocolate foi sorteado!"

# Regras que aparecem no corpo do e-mail (edite à vontade)
REGRAS = """
📅 ENTREGA: 10/04 (sexta-feira) — mais detalhes no grupo

1. O valor mínimo do presente é R$ 30,00 e o máximo é R$ 60,00.
2. Compre algo relacionado às preferências da pessoa.
3. Mantenha segredo até a hora da revelação — nada de spoilers! 🤫
4. Em caso de dúvidas, fale diretamente com quem te enviou esse e-mail.

Boas compras e feliz Páscoa! 🐇
"""

# Colunas de preferência presentes no CSV
COLUNAS_CHOCOLATE = [
    "Chocolate branco",
    "Chocolate ao leite",
    "Chocolate amargo",
    "Chocolate com castanhas",
    "Chocolate com frutas",
]

EMOJIS_NOTA = {1: "😐", 2: "🙂", 3: "😊", 4: "😍", 5: "🤩"} 


# ─────────────────────────────────────────────
#  FUNÇÕES
# ─────────────────────────────────────────────

def nota_para_texto(nota_str: str) -> str:
    """Converte a nota numérica em emoji + descrição."""
    try:
        n = int(nota_str.strip())
        emoji = EMOJIS_NOTA.get(n, "")
        descricoes = {1: "nota dó (1)", 2: "bem meh (2)", 3: "gostozinho (3)", 4: "top (4)", 5: "10/10 (5)"}
        return f"{emoji} {descricoes.get(n, n)}"
    except (ValueError, AttributeError):
        return "—"


def montar_preferencias_html(participante: dict) -> str:
    """Gera o bloco HTML com as preferências de chocolate da pessoa."""
    linhas = ""
    for col in COLUNAS_CHOCOLATE:
        nota_raw = participante.get(col, "").strip()
        texto = nota_para_texto(nota_raw) if nota_raw else "—"
        linhas += f"""
        <tr>
          <td style="padding:6px 12px; border-bottom:1px solid #f0e0c8;">{col}</td>
          <td style="padding:6px 12px; border-bottom:1px solid #f0e0c8;">{texto}</td>
        </tr>"""

    obs = participante.get("Alergias e observações", "").strip()
    obs_html = ""
    if obs and obs.lower() not in ("", "nada", "nenhuma"):
        obs_html = f"""
        <p style="margin-top:12px;">
          <strong>⚠️ Alergias / Observações:</strong><br>
          <span style="color:#c0392b;">{obs}</span>
        </p>"""

    return f"""
    <table style="width:100%; border-collapse:collapse; font-size:14px;">
      <thead>
        <tr style="background:#5d2e0c; color:#fff;">
          <th style="padding:8px 12px; text-align:left;">Tipo de chocolate</th>
          <th style="padding:8px 12px; text-align:left;">Preferência</th>
        </tr>
      </thead>
      <tbody>{linhas}
      </tbody>
    </table>
    {obs_html}
    """


def ler_participantes(caminho_csv: str) -> list[dict]:
    """Lê o CSV e retorna lista de dicts com todos os campos."""
    participantes = []
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            nome  = linha.get("Nome", "").strip()
            email = linha.get("email", "").strip()
            if not nome or not email:
                continue
            p = {"nome": nome, "email": email}
            for col in COLUNAS_CHOCOLATE:
                p[col] = linha.get(col, "").strip()
            p["Alergias e observações"] = linha.get("Alergias e observações", "").strip()
            participantes.append(p)

    if len(participantes) < 2:
        raise ValueError("É preciso ao menos 2 participantes no CSV.")
    return participantes


def sortear(participantes: list[dict], max_tentativas: int = 1000) -> dict[str, str]:
    """
    Sorteia pares (doador → presenteado) evitando:
      - alguém tirar a si mesmo
      - duplas inversas (A→B e B→A simultaneamente)
    """
    nomes = [p["nome"] for p in participantes]

    for _ in range(max_tentativas):
        destinos = nomes[:]
        random.shuffle(destinos)

        if any(nomes[i] == destinos[i] for i in range(len(nomes))):
            continue

        pares = set(zip(nomes, destinos))
        if any((b, a) in pares for (a, b) in pares):
            continue

        return dict(zip(nomes, destinos))

    raise RuntimeError(
        "Não foi possível gerar um sorteio válido. "
        "Verifique se há participantes suficientes."
    )


def montar_email(doador: dict, presenteado: dict) -> str:
    """Monta o corpo do e-mail em HTML."""
    prefs_html = montar_preferencias_html(presenteado)
    return f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; background:#fff;">

  <div style="background:#5d2e0c; padding:24px; border-radius:8px 8px 0 0; text-align:center;">
    <h1 style="color:#fff; margin:0; font-size:28px;">🍫 Amigo de Chocolate</h1>
  </div>

  <div style="padding: 24px; border: 1px solid #e8d5c0; border-top: none; border-radius: 0 0 8px 8px;">

    <h2 style="color:#5d2e0c;">Olá, {doador['nome']}! 👋</h2>
    <p>O sorteio foi realizado e você tirou:</p>

    <div style="background:#fff8f0; border-left:5px solid #e67e22;
                padding:16px; margin:16px 0; border-radius:4px;">
      <p style="margin:0; font-size:20px; font-weight:bold; color:#e67e22;">
        🎯 {presenteado['nome']}
      </p>
    </div>

    <p><strong>🍫 Preferências de chocolates de {presenteado['nome']}:</strong></p>
    {prefs_html}

    <hr style="border:none; border-top:1px solid #e8d5c0; margin:24px 0;">

    <h3 style="color:#5d2e0c;">📋 REGRAS DO AMIGO DE CHOCOLATE 🍫 </h3>
    <div style="background:#fdf8f4; padding:16px; border-radius:4px;
                font-size:14px; white-space:pre-line;">
{REGRAS.strip()}
    </div>

    <p style="color:#aaa; font-size:12px; margin-top:32px; text-align:center;">
      E-mail enviado automaticamente pelo mestre da cerimônia.<br>
      Não responda — mantenha o segredo! 🤫
    </p>

  </div>
</body>
</html>
"""


def enviar_email(destinatario_email: str, assunto: str, corpo_html: str):
    """Envia um e-mail via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = GMAIL_REMETENTE
    msg["To"]      = destinatario_email

    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(GMAIL_REMETENTE, GMAIL_SENHA_APP)
        servidor.sendmail(GMAIL_REMETENTE, destinatario_email, msg.as_string())


def enviar_email_teste():
    """Envia um e-mail de teste para o mestre com dados simulados, validando formatação."""
    # Dados simulados para teste
    doador = {
        "nome": "João Silva (TESTE)",
        "email": GMAIL_REMETENTE,
        "Chocolate branco": "2",
        "Chocolate ao leite": "5",
        "Chocolate amargo": "3",
        "Chocolate com castanhas": "4",
        "Chocolate com frutas": "1",
        "Alergias e observações": "Sem restrições"
    }
    presenteado = {
        "nome": "Maria Santos (TESTE)",
        "email": GMAIL_REMETENTE,
        "Chocolate branco": "5",
        "Chocolate ao leite": "4",
        "Chocolate amargo": "1",
        "Chocolate com castanhas": "",
        "Chocolate com frutas": "3",
        "Alergias e observações": "Alérgica a amendoim"
    }

    # Monta o e-mail usando o template real, mas indicando que é teste
    corpo_html = montar_email(doador, presenteado)
    
    # Insere aviso de teste no início do corpo
    corpo_html = corpo_html.replace(
        "<h2 style=\"color: #c0392b;\">🎁 Olá",
        "<div style=\"background:#fff3cd; border-left: 4px solid #ff9800; padding: 12px; margin: 16px 0; border-radius: 4px; color: #856404;\">"
        "<strong>⚠️ ESTE É UM E-MAIL DE TESTE</strong><br>"
        "Verifique se a formatação e os dados aparecem corretamente."
        "</div>"
        "\n  <h2 style=\"color: #c0392b;\">🎁 Olá"
    )

    try:
        enviar_email(GMAIL_REMETENTE, "🧪 [TESTE] Seu Amigo Secreto foi sorteado!", corpo_html)
        print("✅ E-mail de teste enviado com sucesso para o mestre!")
        print("   Verifique a formatação, dados simulados e se todos os elementos HTML aparecem corretamente.")
        return True
    except Exception as e:
        print(f"❌ Falha ao enviar e-mail de teste: {e}")
        return False


# ─────────────────────────────────────────────
#  PROGRAMA PRINCIPAL
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python amigo_secreto.py participantes.csv")
        print("  python amigo_secreto.py --teste")
        sys.exit(1)

    # Comando: --teste (envia e-mail de teste)
    if sys.argv[1] == "--teste":
        print("📧 Enviando e-mail de teste...\n")
        enviar_email_teste()
        return

    caminho_csv = sys.argv[1]
    print(f"\n📋 Lendo participantes de '{caminho_csv}'...")
    participantes = ler_participantes(caminho_csv)
    por_nome = {p["nome"]: p for p in participantes}

    print(f"✅ {len(participantes)} participantes encontrados.")
    print("\n🎲 Realizando o sorteio...")
    resultado = sortear(participantes)

    print("\n📬 Enviando e-mails...\n")

    erros = []
    for doador_nome, presenteado_nome in resultado.items():
        doador      = por_nome[doador_nome]
        presenteado = por_nome[presenteado_nome]

        corpo = montar_email(doador, presenteado)
        try:
            enviar_email(doador["email"], ASSUNTO_EMAIL, corpo)
            print(f"    ✉️  E-mail enviado para {doador['email']}")
        except Exception as e:
            print(f"    ❌ Falha ao enviar para {doador['email']}: {e}")
            erros.append(doador_nome)

    print("\n" + "─" * 50)
    if erros:
        print(f"⚠️  Sorteio concluído com erros em: {', '.join(erros)}")
    else:
        print("🎉 Sorteio concluído! Todos os e-mails foram enviados com sucesso.")


if __name__ == "__main__":
    main()
