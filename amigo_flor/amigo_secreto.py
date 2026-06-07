"""
🌸 Sorteio de Amigo Secreto de Flores
===================================
Uso:
    python amigo_secreto.py participantes.csv

O CSV deve ter as colunas: nome, email

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

ASSUNTO_EMAIL = "🌸 Seu Amigo Secreto de Flores foi sorteado!"

# Regras que aparecem no corpo do e-mail (edite à vontade)
REGRAS = """
📅 ENCONTRO: 12/06 (Dia dos Namorados)

1. Cada participante deve levar UMA flor que, ao vê-la, lhe lembre a pessoa que você tirou.
2. Mantenha segredo até o momento da troca — nada de spoilers! 🤫

Se tiver dúvidas, entre em contato com a organizadora.
"""


# ─────────────────────────────────────────────
#  FUNÇÕES
# ─────────────────────────────────────────────

def montar_preferencias_html(participante: dict) -> str:
        """Placeholder: não usamos preferências neste sorteio de flores."""
        return ""


def ler_participantes(caminho_csv: str) -> list[dict]:
    """Lê o CSV e retorna lista de dicts com `nome` e `email`.

    Aceita colunas com maiúsculas ou minúsculas (Nome, nome, name) e
    email/E-mail/EMAIL.
    """
    participantes = []
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            nome = (linha.get("Nome") or linha.get("nome") or linha.get("name") or "").strip()
            email = (linha.get("email") or linha.get("Email") or linha.get("E-mail") or "").strip()
            if not nome or not email:
                continue
            participantes.append({"nome": nome, "email": email})

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
        """Monta o corpo do e-mail em HTML para o sorteio de flores."""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; background:#fff;">

    <div style="background:#b53c7a; padding:24px; border-radius:8px 8px 0 0; text-align:center;">
        <h1 style="color:#fff; margin:0; font-size:28px;">🌸 Amigo Secreto de Flores</h1>
    </div>

    <div style="padding: 24px; border: 1px solid #f2d7e7; border-top: none; border-radius: 0 0 8px 8px;">

        <h2 style="color:#b53c7a;">Olá, {doador['nome']}! 👋</h2>
        <p>O sorteio foi realizado e você tirou:</p>

        <div style="background:#fff6fb; border-left:5px solid #e91e63;
                                padding:16px; margin:16px 0; border-radius:4px;">
            <p style="margin:0; font-size:20px; font-weight:bold; color:#e91e63;">
                🌷 {presenteado['nome']}
            </p>
        </div>

        <p><strong>Instrução:</strong> traga uma flor que, ao vê-la, lhe lembre a pessoa que você tirou.</p>

        <hr style="border:none; border-top:1px solid #f2d7e7; margin:24px 0;">

        <h3 style="color:#b53c7a;">📋 Regras</h3>
        <div style="background:#fff6fb; padding:16px; border-radius:4px; font-size:14px; white-space:pre-line;">
{REGRAS.strip()}
        </div>

        <p style="color:#aaa; font-size:12px; margin-top:32px; text-align:center;">
            E-mail enviado automaticamente pela organizadora.<br>
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
    # Dados simulados para teste — apenas nome e email são necessários
    doador = {"nome": "Teste Doadora", "email": GMAIL_REMETENTE}
    presenteado = {"nome": "Teste Presenteada", "email": GMAIL_REMETENTE}

    corpo_html = montar_email(doador, presenteado)

    # Aviso simples de teste
    corpo_html = (
        "<div style=\"background:#fff3cd; padding:12px; border-left:4px solid #ff9800; margin:12px 0;\">"
        "<strong>⚠️ ESTE É UM E-MAIL DE TESTE</strong>"
        "</div>" + corpo_html
    )

    try:
        enviar_email(GMAIL_REMETENTE, "🧪 [TESTE] Seu Amigo Secreto de Flores foi sorteado!", corpo_html)
        print("✅ E-mail de teste enviado com sucesso para o mestre!")
        print("   Verifique a formatação e se os dados aparecem corretamente.")
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
