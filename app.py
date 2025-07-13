import gradio as gr
import os
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, DateTime

"""
app.py — versión 2

👉 Cambios clave respecto a la primera versión
------------------------------------------------
1. Ya **no** hay `PRODUCT_ID` fijo. El ID, título y URL del producto vienen en los *query-params* de la URL que abre Shopify.
2. Se añaden dos columnas nuevas (`product_title`, `product_url`) a la tabla para guardarlas.
3. La función `register_interest` recibe el objeto `gr.Request`, lee `request.query_params` y guarda esos datos.
4. Un pequeño `app.load()` actualiza el encabezado (“## Alerta de precio para…”) cuando la página se carga.
"""

# ---------- Configuración base de datos ----------
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

metadata.create_all(engine)  # crea / actualiza la tabla si falta

# ---------- Lógica ----------

def register_interest(email: str, price: float, request: gr.Request) -> str:  # <- request llega automático
    """Guarda la alerta y devuelve un mensaje de confirmación."""
    dec_price = Decimal(price).quantize(Decimal("0.01"))
    now = datetime.now(datetime.timezone.utc)

    params = request.query_params
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

    nice_name = product_title or product_id
    return (
        f"¡Gracias! Hemos registrado tu alerta para «{nice_name}» a {dec_price} €. "
        "Te avisaremos cuando se alcance."
    )

# ---------- Interfaz Gradio ----------
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

    # Dinamiza el encabezado según los query-params
    def _show_header(request: gr.Request):
        pid = request.query_params.get("product_id", "Producto")
        title = request.query_params.get("product_title")
        name = title or f"ID {pid}"
        return f"## Alerta de precio para **{name}**"

    app.load(fn=_show_header, inputs=None, outputs=header_md)

    submit_btn.click(register_interest, inputs=[email_input, price_input], outputs=out_box)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 7860))   # Render define PORT en runtime
    app.launch(server_name="0.0.0.0", server_port=port)
