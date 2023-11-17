"""migrate to new form

修订 ID: 14ab5b50ede5
父修订:
创建时间: 2023-10-11 14:44:00.050704

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "14ab5b50ede5"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_UPGRADE_SQL = """
INSERT INTO "user" ("user", "access_token") (
    SELECT
        CASE WHEN "qq_id" IS NOT NULL THEN
            jsonb_build_object('type', 'qq_user', 'qq_user_id', "qq_id")
        ELSE
            jsonb_build_object('type', 'qqguild_user', 'qqguild_user_id', "qqguild_id")
        END,
        "access_token"
    FROM "user_old" WHERE "qq_id" IS NOT NULL OR "qqguild_id" IS NOT NULL
);
"""
GROUP_UPGRADE_SQL = """
INSERT INTO "group" ("group", "bind_repo") (
    SELECT
        jsonb_build_object('type', 'qq_group', 'qq_group_id', "qq_group"), "bind_repo"
    FROM "group_old" WHERE "qq_group" IS NOT NULL
);
"""
USER_SUBSCRIPTION_UPGRADE_SQL = """
INSERT INTO "subscription" ("subscriber", "owner", "repo", "event", "action") (
    SELECT
        jsonb_build_object('type', 'qq_user', 'qq_user_id', "qq_id"),
        "owner", "repo", "event", array_agg("a")
    FROM "user_subscription", LATERAL jsonb_array_elements_text("action") AS actions(a)
    WHERE "qq_id" IS NOT NULL
    GROUP BY "owner", "repo", "event", "qq_id"
);
"""
GROUP_SUBSCRIPTION_UPGRADE_SQL = """
INSERT INTO "subscription" ("subscriber", "owner", "repo", "event", "action") (
    SELECT
        jsonb_build_object('type', 'qq_group', 'qq_group_id', "qq_group"),
        "owner", "repo", "event", array_agg("a")
    FROM "group_subscription", LATERAL jsonb_array_elements_text("action") AS actions(a)
    WHERE "qq_group" IS NOT NULL
    GROUP BY "owner", "repo", "event", "qq_group"
);
"""


def upgrade(name: str = "") -> None:
    if name:
        return

    conn = op.get_bind()
    tables = sa.inspect(conn).get_table_names()

    # ### commands auto generated by Alembic - please adjust! ###

    # Drop old version aerich table
    if "aerich" in tables:
        op.drop_table("aerich")

    # create new subscription table
    op.create_table(
        "subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "subscriber", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("owner", sa.String(), nullable=False),
        sa.Column("repo", sa.String(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("action", postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription")),
        sa.UniqueConstraint(
            "subscriber",
            "owner",
            "repo",
            "event",
            name=op.f("uq_subscription_subscriber"),
        ),
    )
    with op.batch_alter_table("subscription", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_subscription_owner"),
            ["owner", "repo", "event", "action"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_subscription_subscriber"), ["subscriber"], unique=False
        )

    # migrate data from old table to new table
    if "user_subscription" in tables:
        op.execute(USER_SUBSCRIPTION_UPGRADE_SQL)

        with op.batch_alter_table("user_subscription", schema=None) as batch_op:
            batch_op.drop_index("idx_user_subscr_owner_dce522")
            batch_op.drop_index("idx_user_subscr_qq_id_d076c7")
            batch_op.drop_index("idx_user_subscr_qqguild_f24790")

        op.drop_table("user_subscription")

    if "group_subscription" in tables:
        op.execute(GROUP_SUBSCRIPTION_UPGRADE_SQL)

        with op.batch_alter_table("group_subscription", schema=None) as batch_op:
            batch_op.drop_index("idx_group_subsc_owner_071a60")
            batch_op.drop_index("idx_group_subsc_qq_grou_9d77e0")
            batch_op.drop_index("idx_group_subsc_qqguild_8a9fcf")

        op.drop_table("group_subscription")

    # migrate user table
    HAS_OLD_USER = "user" in tables
    if HAS_OLD_USER:
        op.rename_table("user", "user_old")

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("access_token", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
    )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_user"), ["user"], unique=True)

    if HAS_OLD_USER:
        op.execute(USER_UPGRADE_SQL)
        op.drop_table("user_old")

    # migrate group table
    HAS_OLD_GROUP = "group" in tables
    if HAS_OLD_GROUP:
        op.rename_table("group", "group_old")

    op.create_table(
        "group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("bind_repo", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_group")),
    )
    with op.batch_alter_table("group", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_group_group"), ["group"], unique=True)

    if HAS_OLD_GROUP:
        op.execute(GROUP_UPGRADE_SQL)
        op.drop_table("group_old")

    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return

    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("group", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_group_group"))

    op.drop_table("group")

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_user"))

    op.drop_table("user")

    with op.batch_alter_table("subscription", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_subscription_subscriber"))
        batch_op.drop_index(batch_op.f("ix_subscription_owner"))

    op.drop_table("subscription")
    # ### end Alembic commands ###
