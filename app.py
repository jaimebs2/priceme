import os
os.environ["GRADIO_DEFAULT_LOCALE"] = "en"  # Idioma por defecto para evitar fallo svelte-i18n

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import gradio as gr
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
)

"""
app.py — versión 5 (simplificada)
--------------------------------
• Elimina FastAPI/mount para volver a `app.launch()` → evita redirecciones 307.
• Mantiene arreglos: normalizar `postgres://`, `pool_pre_ping`, timezone.utc.
• Sigue usando GRADIO_DEFAULT_LOCALE="en" para Chrome/Edge.
"""

# ------------- Configuración BD ----------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///price_requests.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
metadata = MetaData()

price_requests = Table(
    "price_requests",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("product_id", String, nullable=False),
    Column("product_title", String, nullable=True),
    Column("product_url", String, nullable=True),
    Column("email", String, nullable=False),
    Column("desired_price", Numeric(10, 2), nullable=False),
    Column("requested_at", DateTime, nullable=False),
)
metadata.create_all(engine)

# ------------- Lógica --------------------------------------

def register_interest(email: str, price: float, request: gr.Request | None = None) -> str:
    dec_price = Decimal(price).quantize(Decimal("0.01"))
    now = datetime.now(timezone.utc)

    params = request.query_params if request else {}
    product_id = params.get("product_id", "UNKNOWN")
    product_title = params.get("product_title", "")
    product_url = params.get("product_url", "")

    with engine.begin() as conn:
        conn.execute(
            price_requests.insert().values(
                product_id=product_id,
                product_title=product_title,
                product_url=product_url,
                email=email,
                desired_price=dec_price,
                requested_at=now,
            )
        )

    nombre = product_title or product_id
    return f"¡Guardado! Te avisaremos cuando «{nombre}» cueste {dec_price} €."

# ------------- Interfaz Gradio ------------------------------
with gr.Blocks(title="Alerta de precio") as app:
    header_md = gr.Markdown()

    email_input = gr.Textbox(label="Correo electrónico", placeholder="tucorreo@ejemplo.com")
    price_input = gr.Number(label="Precio objetivo (€)", minimum=0, precision=2)
    submit_btn = gr.Button("Registrar alerta", variant="primary")
    out_box = gr.Textbox(label="Estado", interactive=False)

    def _show_header(request: gr.Request | None = None):
        if request is None:
            return "## Alerta de precio"
        pid = request.query_params.get("product_id", "Producto")
        title = request.query_params.get("product_title")
        nombre = title or f"ID {pid}"
        return f"## Alerta de precio para **{nombre}**"

    app.load(fn=_show_header, inputs=None, outputs=header_md)
    submit_btn.click(register_interest, inputs=[email_input, price_input], outputs=out_box)

# ------------- Arranque ------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)