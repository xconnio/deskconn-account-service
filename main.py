from xconn import App
from xconn.app import ExecutionMode

from deskconn.database import database
from deskconn.api.auth import component as auth_component
from deskconn.api.user import component as user_component
from deskconn.api.device import component as device_component
from deskconn.api.desktop import component as desktop_component
from deskconn.api.organization import component as organization_component


app = App()
app.set_execution_mode(ExecutionMode.ASYNC)


async def on_startup():
    await database.init_db()


app.add_event_handler("startup", on_startup)

app.include_component(user_component)
app.include_component(auth_component)
app.include_component(device_component)
app.include_component(desktop_component)
app.include_component(organization_component)
app.set_schema_procedure("io.xconn.deskconn.account.schema.get")
