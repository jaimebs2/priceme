import gradio as gr
import os
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, DateTime

"""
app.py — versión 3  (manejo de "request == None" y PORT dinámico)
---------------------------------------------------------------
Soluciona el error:
    AttributeError: 'NoneType' object has no attribute 'query_params'
que aparece cuando Gradio llama a _show_header sin request.

Cambios:
1. Todas las funciones aceptan `request: gr.Request | None` y manejan el caso `None`.
2. Puerto leído de la variable de entorno `PORT` (Render lo define).
3. Mensaje de confirmación simplificado.
"""

# ---------------- Base de datos ----------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///price_requests.db")
engine = create_engine(DATABASE_URL)
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

# ---------------- Lógica -----------------------------------

def register_interest(email: str, price: float, request: gr.Request | None = None) -> str:
    dec_price = Decimal(price).quantize(Decimal("0.01"))
    now = datetime.utcnow()

    # Valores por defecto si no vienen query-params
    product_id = "UNKNOWN"
    product_title = ""
    product_url = ""

    if request is not None:
        params = request.query_params
        product_id = params.get("product_id", product_id)
        product_title = params.get("product_title", product_title)
        product_url = params.get("product_url", product_url)

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

# ---------------- Interfaz Gradio --------------------------
with gr.Blocks(title="Alerta de precio") as app:
    header_md = gr.Markdown()

    email_input = gr.Textbox(
        label="Correo electrónico",
        placeholder="tucorreo@ejemplo.com",
        elem_id="email",
    )
    price_input = gr.Number(label="Precio objetivo (€)", minimum=0, precision=2, elem_id="price")

    submit_btn = gr.Button("Registrar alerta", variant="primary")
    out_box = gr.Textbox(label="Estado", interactive=False)

    def _show_header(request: gr.Request | None = None):
        """Devuelve el título dinámico o uno genérico si no hay request."""
        if request is None:
            return "## Alerta de precio"
        pid = request.query_params.get("product_id", "Producto")
        title = request.query_params.get("product_title")
        nombre = title or f"ID {pid}"
        return f"## Alerta de precio para **{nombre}**"

    app.load(fn=_show_header, inputs=None, outputs=header_md)
    submit_btn.click(register_interest, inputs=[email_input, price_input], outputs=out_box)

# ---------------- Arranque ---------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))  # Render define $PORT
    app.launch(server_name="0.0.0.0", server_port=port)
