import os
import httpx

from urllib.parse import urlparse

from nebula.config import config
from nebula.log import log
from nebula.common import import_module

from nebula.settings.models import (
    ActionSettings,
    FolderSettings,
    PlayoutChannelSettings,
    ServiceSettings,
    StorageSettings,
    ViewSettings,
)

from setup.defaults.actions import ACTIONS
from setup.defaults.channels import CHANNELS
from setup.defaults.folders import FOLDERS
from setup.defaults.services import SERVICES
from setup.defaults.views import VIEWS
from setup.defaults.meta_types import META_TYPES

from setup.metatypes import setup_metatypes


TEMPLATE = {
    "actions": ACTIONS,
    "channels": CHANNELS,
    "folders": FOLDERS,
    "services": SERVICES,
    "views": VIEWS,
    "meta_types": META_TYPES,
    "storages": [],
}


def load_overrides():
    if not os.path.isdir("/settings"):
        return
    for fname in os.listdir("/settings"):
        spath = os.path.join("/settings", fname)
        sname, sext = os.path.splitext(spath)
        if sext != ".py":
            continue
        mod = import_module(sname, spath)

        for key in TEMPLATE:
            if not hasattr(mod, key.upper()):
                continue
            log.info(f"Using settings overrides: {spath}")
            TEMPLATE[key] = getattr(mod, key.upper())


async def setup_settings(db):

    load_overrides()

    log.info("Applying system settings")
    settings: dict[str, any] = {}

    # Nebula 5 compat
    redis_url = urlparse(config.redis)
    settings["redis_host"] = redis_url.hostname
    settings["redis_port"] = redis_url.port or 6379
    settings["site_name"] = config.site_name

    for key, value in settings.items():
        await db.execute(
            """
            INSERT INTO settings (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value=$2
            """,
            key,
            value,
        )
    log.trace(f"Saved {len(settings)} system settings")

    # Setup views

    await db.execute("DELETE FROM views")
    for view in TEMPLATE["views"]:
        assert isinstance(view, ViewSettings)
        vdata = view.dict(exclude_none=True)
        vid = vdata.pop("id")

        await db.execute(
            """
            INSERT INTO views (id, settings)
            VALUES ($1, $2)
            """,
            vid,
            vdata,
        )
    await db.execute(
        """
        SELECT setval(pg_get_serial_sequence('views', 'id'),
        coalesce(max(id),0) + 1, false) FROM views;
        """
    )
    log.trace(f"Saved {len(TEMPLATE['views'])} views")

    # Setup folders

    await db.execute("DELETE FROM folders")
    for folder in TEMPLATE["folders"]:
        assert isinstance(folder, FolderSettings)
        fdata = folder.dict(exclude_none=True)
        fid = fdata.pop("id")

        await db.execute(
            """
            INSERT INTO folders (id, settings)
            VALUES ($1, $2)
            """,
            fid,
            fdata,
        )
    await db.execute(
        """
        SELECT setval(pg_get_serial_sequence('folders', 'id'),
        coalesce(max(id),0) + 1, false) FROM folders;
        """
    )
    log.trace(f"Saved {len(TEMPLATE['folders'])} folders")

    # Setup metatypes

    await setup_metatypes(TEMPLATE["meta_types"], db)
    log.trace(f"Saved {len(TEMPLATE['meta_types'])} meta types")

    # Setup classifications

    classifications = []
    async with httpx.AsyncClient() as client:
        response = await client.get("https://cs.nbla.xyz/dump")
        classifications = response.json()

    for scheme in classifications:
        name = scheme["cs"]
        await db.execute("DELETE FROM cs WHERE cs = $1", name)
        for value in scheme["data"]:
            settings = scheme["data"][value]
            await db.execute(
                "INSERT INTO cs(cs, value, settings) VALUES ($1, $2, $3)",
                name,
                value,
                settings,
            )
    log.trace(f"Saved {len(classifications)} classifications")

    # Setup services

    for service in TEMPLATE["services"]:
        assert isinstance(service, ServiceSettings)
        await db.execute(
            """
            INSERT INTO services
            (id, service_type, host, title, settings, autostart, loop_delay)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (id) DO UPDATE SET
            service_type=$2, host=$3, title=$4, settings=$5, autostart=$6, loop_delay=$7
            """,
            service.id,
            service.type,
            service.host,
            service.name,
            service.settings,
            service.autostart,
            service.loop_delay,
        )
    await db.execute(
        """
        SELECT setval(pg_get_serial_sequence('services', 'id'),
        coalesce(max(id),0) + 1, false) FROM services;
        """
    )
    log.trace(f"Saved {len(TEMPLATE['services'])} services")

    # Setup actions

    for action in TEMPLATE["actions"]:
        assert isinstance(action, ActionSettings)
        await db.execute(
            """
            INSERT INTO actions
            (id, service_type, title, settings)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET
            service_type=$2, title=$3, settings=$4
            """,
            action.id,
            action.type,
            action.name,
            action.settings,
        )
    await db.execute(
        """
        SELECT setval(pg_get_serial_sequence('actions', 'id'),
        coalesce(max(id),0) + 1, false) FROM actions;
        """
    )
    log.trace(f"Saved {len(TEMPLATE['actions'])} actions")

    # Setup channels

    for channel in TEMPLATE["channels"]:
        assert isinstance(channel, PlayoutChannelSettings)
        channel_data = channel.dict()
        id_channel = channel_data.pop("id", None)
        await db.execute(
            """
            INSERT INTO channels (id, channel_type, settings)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET
            channel_type=$2, settings=$3
            """,
            id_channel,
            0,
            channel_data,
        )
    await db.execute(
        """
        SELECT setval(pg_get_serial_sequence('channels', 'id'),
        coalesce(max(id),0) + 1, false) FROM channels;
        """
    )
    log.trace(f"Saved {len(TEMPLATE['channels'])} channels")

    # Setup storages

    for storage in TEMPLATE["storages"]:
        assert isinstance(storage, StorageSettings)
        storage_data = storage.dict()
        id_storage = storage_data.pop("id", None)
        await db.execute(
            """
            INSERT INTO storages (id, settings)
            VALUES ($1, $2)
            ON CONFLICT (id) DO UPDATE SET
            settings=$2
            """,
            id_storage,
            storage_data,
        )
    await db.execute(
        """
        SELECT setval(pg_get_serial_sequence('storages', 'id'),
        coalesce(max(id),0) + 1, false) FROM storages;
        """
    )
    log.trace(f"Saved {len(TEMPLATE['storages'])} storages")