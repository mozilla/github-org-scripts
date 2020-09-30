# disable browser launch (it's in a container)
c.NotebookApp.open_browser = False
# Set connection string
c.NotebookApp.portInt = 10001
c.NotebookApp.custom_display_url = 'http://localhost:10001'
# disable security locally
# non-empty token to avoid missing _xsrf on POST (from
# https://github.com/nteract/hydrogen/issues/922#issuecomment-315665849)
c.NotebookApp.token = 'xx'
c.NotebookApp.password = ''
