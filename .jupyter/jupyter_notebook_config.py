# disable browser launch (it's in a container)
c.NotebookApp.open_browser = False
# Set connection string
#c.NotebookApp.portInt = 10002
c.NotebookApp.custom_display_url = 'http://localhost:10002'
# disable security locally
c.NotebookApp.token = ''
c.NotebookApp.password = ''
