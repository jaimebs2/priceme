<script>
function abreGradio(){
  const features = [
    'width=500','height=650',
    'menubar=no','toolbar=no',
    'resizable=yes','scrollbars=yes',
    'noopener'            // evita bloqueo COOP
  ].join(',');
  window.open('https://mi-gradio-eta.vercel.app', 'mini', features);
}
</script>

<button class="addon-button" onclick="abreGradio()">Consultar IA</button>