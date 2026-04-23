#sqlalchemy table defs
from sqlalchemy import Integer, String, Boolean, JSON, TIMESTAMP, text, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.mutable import MutableDict


class Base(DeclarativeBase):
  pass


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(50),primary_key=True)

    #server configs
    cores: Mapped[int] = mapped_column(Integer, default=1)
    memory_gb: Mapped[int] = mapped_column(Integer, default=4)

#code config settings, given its own table for making presets at a later date
class Code_Configs(Base):
    __tablename__ = "Code_Configs"

    #email plus a presetID gives the config set to use
    preset_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255))
    
    #show which config is active and allow users to name them.
    preset_name: Mapped[str] = mapped_column(String(255), default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))
    upload_dir: Mapped[str] = mapped_column(String(255))
    last_fem: Mapped[str] = mapped_column(String(255), nullable = True)
    last_floorplan: Mapped[str] = mapped_column(String(255), nullable = True)
    last_power_trace: Mapped[str] = mapped_column(String(255), nullable = True)


    __table_args__ = (
        ForeignKeyConstraint(
            ['email', ],           
            ['users.email'] 
        ),
    )

#training and post processing broken up into seperate table for easier data manipulation, no sense in grabbing all these values if not needed.
#own table may also allow users to have multiple jobs running at a later date.
class Training_Data(Base):
    __tablename__ = "single_block_data"

    email: Mapped[str] = mapped_column(String(50),primary_key=True)
    

    have_A_matrix: Mapped[bool] = mapped_column(Boolean, default=False)
    have_eigenvalues: Mapped[bool] = mapped_column(Boolean, default=False)
    looked_at_eigen: Mapped[bool] = mapped_column(Boolean,default = False)
    have_pod_modes: Mapped[bool] = mapped_column(Boolean, default=False)
    have_C_matrix: Mapped[bool] = mapped_column(Boolean, default=False)
    have_G_matrix: Mapped[bool] = mapped_column(Boolean, default=False)
    have_P_matrix: Mapped[bool] = mapped_column(Boolean, default=False)
    have_ODE_sol: Mapped[bool] = mapped_column(Boolean, default=False)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['email', ],           
            ['users.email'] 
        ),
    )

class Post_Processing_Data(Base):
    __tablename__ = "post_processing_data"
    email: Mapped[str] = mapped_column(String(50),primary_key=True)
    whole_mesh_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    slice_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ['email', ],           
            ['users.email'] 
        ),
    )




