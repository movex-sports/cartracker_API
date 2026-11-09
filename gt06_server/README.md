# Receptor TCP GT06

Receptor de diagnóstico para rastreadores G900L/J16. Ele aceita conexões TCP,
remonta pacotes fragmentados, valida CRC-16/X25, identifica o IMEI, decodifica
pacotes básicos e envia ACK para login e heartbeat.

## Executar

```powershell
cd gt06_server
$env:GT06_PORT = "5023"
python server.py
```

Libere a porta escolhida no firewall somente quando for realizar um teste
controlado. Para receber dados pela rede móvel, o endereço e a porta precisam
ser públicos e encaminhados para este processo.

Cada pacote é registrado em hexadecimal. Protocolos desconhecidos também são
preservados no log para que a variante de firmware do aparelho possa ser
implementada sem perda de dados.

## Testar

```powershell
python -m unittest -v test_gt06.py
```

Esta primeira versão não publica posições automaticamente na API. Alguns
firmwares J16 enviam ignição e bateria em extensões diferentes; primeiro é
necessário capturar uma sessão real para confirmar os campos antes de gravá-los.
