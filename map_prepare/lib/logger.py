import logging
from sys import stdout

handler = logging.FileHandler(filename='./map-prepare.log', encoding='utf-8', mode='w+')
# handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s | %(name)s: %(message)s'))

app_log = logging.getLogger('app')
app_log.setLevel(logging.INFO)

# handler = logging.FileHandler(filename='./app.log', encoding='utf-8', mode='w+')
# Use one formatting for all outputs
formatting = '[%(relativeCreated)d] [%(processName)s] %(levelname)s | %(filename)s : %(message)s'
handler.setFormatter(logging.Formatter(formatting))
app_log.addHandler(handler)
console_handler = logging.StreamHandler(stream=stdout)
console_handler.setFormatter(logging.Formatter(formatting))
app_log.addHandler(console_handler)

debug = app_log.debug
info = app_log.info
warn = app_log.warn
error = app_log.error
fatal = app_log.critical