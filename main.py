from xconn import App
from xconn.app import ExecutionMode

from deskconn.api.auth import component as auth_component
from deskconn.api.user import component as user_component
from deskconn.api.coturn import component as coturn_component
from deskconn.api.device import component as device_component
from deskconn.api.desktop import component as desktop_component
from deskconn.api.principal import component as principal_component
from deskconn.api.organization import component as organization_component
from deskconn.api.update import component as update_component
from deskconn.api.migrate import component as migrate_component


app = App()
app.set_execution_mode(ExecutionMode.ASYNC)


app.include_component(user_component)
app.include_component(auth_component)
app.include_component(coturn_component)
app.include_component(device_component)
app.include_component(desktop_component)
app.include_component(principal_component)
app.include_component(organization_component)
app.include_component(update_component)
app.include_component(migrate_component)
app.set_schema_procedure("io.xconn.deskconn.account.schema.get")
