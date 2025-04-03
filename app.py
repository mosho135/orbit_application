import datetime as dt
import hmac

import folium
import streamlit as st
from folium.plugins import MarkerCluster
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder
from streamlit_folium import st_folium

from data_sets import (get_in_plan, get_out_of_plan, orbit_active_data,
                       orbit_inactive_data)

today = dt.datetime.today()
today = today.strftime("%Y%m%d%H%M%S")

# Password check


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# TODO: add in the areas for the map view. And look to deploy and web application and test
# TODO: Add a download button for the HTML map for quicker loading time

# set page
st.set_page_config(page_title="Mercedes-Benz Rentention", page_icon="🌎", layout="wide")

# Set page header
st.header("MERCEDES-BENZ - RETENTION", divider="blue")
st.header("")

# Get the data


@st.cache_data
def get_data(d_type):
    if d_type == "OA":
        main_df = orbit_active_data()
        return main_df
    elif d_type == "OI":
        main_df = orbit_inactive_data()
        return main_df


# option menu
from streamlit_option_menu import option_menu

with st.sidebar:
    selected = option_menu(
        menu_title="MAIN MENU",
        options=[
            "Orbit Active Customers",
            "Orbit Inactive Customers",
        ],
        icons=["book", "book"],
        menu_icon="cast",  # option
        default_index=0,  # option
        orientation="vertical",
    )


def av_options(df, options):
    available_options = (df[options].sort_values(ascending=True)).unique().tolist()
    available_options.insert(0, -1)  # Add "All" option represented by -1
    return available_options


def options_select(available_options, selected_key):
    selected_options = st.session_state[selected_key]
    if (
        -1 in selected_options and len(selected_options) > 1
    ):  # "All" and other options selected
        # Deselect all other options except "All"
        st.session_state[selected_key] = [-1]
    elif (
        -1 in selected_options and len(selected_options) == 1
    ):  # Only "All" is selected
        # Ensure "All" stays selected, no changes needed
        return
    elif (
        -1 not in selected_options and len(selected_options) >= 1
    ):  # Other options are selected
        # Deselect "All" if it exists
        if -1 in st.session_state[selected_key]:
            st.session_state[selected_key].remove(-1)


def side_filter_selection(df):
    show_more_filters = st.sidebar.checkbox("Show More Filters", key="show_filter")
    dealer = st.sidebar.multiselect(
        label="Filter Current Dealer",
        options=av_options(df, "Branch"),
        default=[-1],
        key="branch_options",
        on_change=lambda: options_select(av_options(df, "Branch"), "branch_options"),
        format_func=lambda x: "All" if x == -1 else str(x),
    )

    # TODO: Check why the actiontype is not being filtered
    lactiontype = st.sidebar.multiselect(
        label="Filter Last Interaction Type",
        options=av_options(df, "Last_Interaction_Type"),
        default=[-1],
        key="actiontype_options",
        on_change=lambda: options_select(av_options(df, "Last_Interaction_Type"), "actiontype_options"),
        format_func=lambda x: "All" if x == -1 else str(x),
    )

    company = st.sidebar.multiselect(
        label="Filter Company",
        options=av_options(df, "Company"),
        default=[-1],
        key="company_options",
        on_change=lambda: options_select(
            av_options(df, "Company"), "company_options"
        ),
        format_func=lambda x: "All" if x == -1 else str(x),
    )

    sell_dealer = st.sidebar.multiselect(
        label="Filter Selling Dealer",
        options=av_options(df, "Selling_Dealer"),
        default=[-1],
        key="sdealer_options",
        on_change=lambda: options_select(
            av_options(df, "Selling_Dealer"), "sdealer_options"
        ),
        format_func=lambda x: "All" if x == -1 else f"{x}",
    )
    sell_dealer_actiontype = st.sidebar.multiselect(
        label="Filter Selling Dealer New / Used",
        options=av_options(df, "Selling_ActionType"),
        default=[-1],
        key="stype_options",
        on_change=lambda: options_select(
            av_options(df, "Selling_ActionType"), "stype_options"
        ),
        format_func=lambda x: "All" if x == -1 else f"{x}",
    )

    brand = st.sidebar.multiselect(
        label="Filter Brand",
        options=av_options(df, "Brand"),
        default=[-1],
        key="brand_options",
        on_change=lambda: options_select(av_options(df, "Brand"), "brand_options"),
        format_func=lambda x: "All" if x == -1 else f"{x}",
    )

    df_selection = df[
        (df["Branch"].isin(dealer) | (-1 in dealer))
        & (df["Company"].isin(company) | (-1 in company))
        & (df["Last_Interaction_Type"].isin(lactiontype) | (-1 in lactiontype))
        & (df["Selling_Dealer"].isin(sell_dealer) | (-1 in sell_dealer))
        & (df["Selling_ActionType"].isin(sell_dealer_actiontype) | (-1 in sell_dealer_actiontype))
        & (df["Brand"].isin(brand) | (-1 in brand))
    ]

    vehicle = st.sidebar.multiselect(
        label="Filter Model",
        options=av_options(df_selection, "Vehicles"),
        default=[-1],
        key="model_options",
        on_change=lambda: options_select(
            av_options(df_selection, "Vehicles"), "model_options"
        ),
        format_func=lambda x: "All" if x == -1 else f"{x}",
    )

    df_selection = df[
        (df["Branch"].isin(dealer) | (-1 in dealer))
        & (df["Company"].isin(company) | (-1 in company))
        & (df["Last_Interaction_Type"].isin(lactiontype) | (-1 in lactiontype))
        & (df["Selling_Dealer"].isin(sell_dealer) | (-1 in sell_dealer))
        & (
            df["Selling_ActionType"].isin(sell_dealer_actiontype)
            | (-1 in sell_dealer_actiontype)
        )
        & (df["Brand"].isin(brand) | (-1 in brand))
        & (df["Vehicles"].isin(vehicle) | (-1 in vehicle))
    ]

    province = st.sidebar.multiselect(
        label="Filter Province",
        options=av_options(df_selection, "Province"),
        default=[-1],
        key="province_options",
        on_change=lambda: options_select(
            av_options(df_selection, "Province"), "province_options"
        ),
        format_func=lambda x: "All" if x == -1 else f"{x}",
    )

    df_selection = df[
        (df["Branch"].isin(dealer) | (-1 in dealer))
        & (df["Company"].isin(company) | (-1 in company))
        & (df["Last_Interaction_Type"].isin(lactiontype) | (-1 in lactiontype))
        & (df["Selling_Dealer"].isin(sell_dealer) | (-1 in sell_dealer))
        & (
            df["Selling_ActionType"].isin(sell_dealer_actiontype)
            | (-1 in sell_dealer_actiontype)
        )
        & (df["Brand"].isin(brand) | (-1 in brand))
        & (df["Vehicles"].isin(vehicle) | (-1 in vehicle))
        & (df["Province"].isin(province) | (-1 in province))
    ]

    area = st.sidebar.multiselect(
        label="Filter Area",
        options=av_options(df_selection, "Area"),
        default=[-1],
        key="area_options",
        on_change=lambda: options_select(
            av_options(df_selection, "Area"), "area_options"
        ),
        format_func=lambda x: "All" if x == -1 else f"{x}",
    )

    df_selection = df[
        (df["Branch"].isin(dealer) | (-1 in dealer))
        & (df["Company"].isin(company) | (-1 in company))
        & (df["Last_Interaction_Type"].isin(lactiontype) | (-1 in lactiontype))
        & (df["Selling_Dealer"].isin(sell_dealer) | (-1 in sell_dealer))
        & (
            df["Selling_ActionType"].isin(sell_dealer_actiontype)
            | (-1 in sell_dealer_actiontype)
        )
        & (df["Brand"].isin(brand) | (-1 in brand))
        & (df["Vehicles"].isin(vehicle) | (-1 in vehicle))
        & (df["Province"].isin(province) | (-1 in province))
        & (df["Area"].isin(area) | (-1 in area))
    ]

    if st.session_state.show_filter:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            v_age_r = st.multiselect(
                label="Vehicle Age (Reg Date)",
                options=av_options(df_selection, "Vehicle_Age_Reg_Date"),
                default=[-1],
                key="v_age_r_options",
                on_change=lambda: options_select(
                    av_options(df_selection, "Vehicle_Age_Reg_Date"), "v_age_r_options"
                ),
                format_func=lambda x: "All" if x == -1 else f"{x}",
            )
        with col2:
            v_age_p = st.multiselect(
                label="Vehicle Age (Plan End Date)",
                options=av_options(df_selection, "Vehicle_Age_Plan"),
                default=[-1],
                key="v_age_p_options",
                on_change=lambda: options_select(
                    av_options(df_selection, "Vehicle_Age_Plan"), "v_age_p_options"
                ),
                format_func=lambda x: "All" if x == -1 else f"{x}",
            )
        with col3:
            age_group = st.multiselect(
                label="Customer Age Group",
                options=av_options(df_selection, "Age_Group"),
                default=[-1],
                key="age_options",
                on_change=lambda: options_select(
                    av_options(df_selection, "Age_Group"), "age_options"
                ),
                format_func=lambda x: "All" if x == -1 else f"{x}",
            )
        with col4:
            multi_owner = st.multiselect(
                label="Multiple Ownership",
                options=av_options(df_selection, "Multiple_Ownership"),
                default=[-1],
                key="multi_owner_options",
                on_change=lambda: options_select(
                    av_options(df_selection, "Multiple_Ownership"),
                    "multi_owner_options",
                ),
                format_func=lambda x: "All" if x == -1 else f"{x}",
            )
        with col5:
            company_owned = st.multiselect(
                label="Company Owned",
                options=av_options(df_selection, "Company_Owned"),
                default=[-1],
                key="company_owned_options",
                on_change=lambda: options_select(
                    av_options(df_selection, "Company_Owned"), "company_owned_options"
                ),
                format_func=lambda x: "All" if x == -1 else f"{x}",
            )
        df_selection = df[
            (df["Branch"].isin(dealer) | (-1 in dealer))
            & (df["Company"].isin(company) | (-1 in company))
            & (df["Last_Interaction_Type"].isin(lactiontype) | (-1 in lactiontype))
            & (df["Selling_Dealer"].isin(sell_dealer) | (-1 in sell_dealer))
            & (
                df["Selling_ActionType"].isin(sell_dealer_actiontype)
                | (-1 in sell_dealer_actiontype)
            )
            & (df["Brand"].isin(brand) | (-1 in brand))
            & (df["Vehicles"].isin(vehicle) | (-1 in vehicle))
            & (df["Area"].isin(area) | (-1 in area))
            & (df["Vehicle_Age_Reg_Date"].isin(v_age_r) | (-1 in v_age_r))
            & (df["Vehicle_Age_Plan"].isin(v_age_p) | (-1 in v_age_p))
            & (df["Age_Group"].isin(age_group) | (-1 in age_group))
            & (df["Multiple_Ownership"].isin(multi_owner) | (-1 in multi_owner))
            & (df["Company_Owned"].isin(company_owned) | (-1 in company_owned))
        ]

    return df_selection


def metrics(df):
    from streamlit_extras.metric_cards import style_metric_cards

    col1, col2, col3 = st.columns(3)

    col1.metric(
        label="Total Vehicles", value=df["Branch"].count(), delta="All vehicles"
    )

    col2.metric(label="In Plan", value=get_in_plan(df), delta="In Plan")

    col3.metric(label="Out Of Plan", value=get_out_of_plan(df), delta="Out Of Plan")

    style_metric_cards(
        background_color="#ffffff", border_left_color="#18334C", box_shadow="3px"
    )


def table(df):
    shouldDisplayPivoted = st.checkbox("Pivot Table", key="checked")

    gb = GridOptionsBuilder()

    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
    )

    gb.configure_column(
        field="Brand",
        header_name="Brand",
        width=30,
        rowGroup=shouldDisplayPivoted,
        sort="asc",
    )

    gb.configure_column(
        field="Vehicles",
        header_name="Vehicle",
        width=30,
        rowGroup=shouldDisplayPivoted,
        sort="asc",
    )

    gb.configure_column(
        field="Mileage Category",
        header_name="Mileage Category",
        tooltipField="Mileage Category",
        pivot=True,
    )

    gb.configure_column(
        field="Branch",
        header_name="Total",
        width=120,
        aggFunc="count",
        valueFormatter="value.toLocaleString()",
    )

    gb.configure_grid_options(
        tooltipShowDelay=0, pivotMode=shouldDisplayPivoted, suppressAggFuncInHeader=True
    )

    gb.configure_grid_options(
        autoGroupColumnDef=dict(
            minWidth=30, pinned="left", cellRendererParams=dict(suppressCount=True)
        )
    )
    if st.session_state.checked:
        go = gb.build()
        AgGrid(
            df,
            gridOptions=go,
            height=500,
            fit_columns_on_grid_load=ColumnsAutoSizeMode.FIT_CONTENTS,
        )
    else:
        shwdata = st.multiselect(
            "Columns To Show :",
            df.columns,
            default=[
                "Branch",
                "Multiple_Ownership",
                "Company",
                "Company_Owned",
                "Age_Group",
                "Suburb",
                "Area",
                "Last_Interaction_Type",
                "Last Interaction Date",
                "Body Number",
                "1st Section",
                "2nd Section",
                "3rd Section",
                "Vehicle_Age_Reg_Date",
                "Brand",
                "Vehicles",
                "Model",
                "Mileage Category",
                "Ownership",
                "Customer Type",
                "Planned end date",
                "Vehicle_Age_Plan",
                "Plan",
            ],
        )
        AgGrid(df[shwdata], height=500)


def map_data(df, is_gcm="N"):
    df = df.loc[df["Has_Coord"] == "Y"]
    a_keys = ("latitude", "longitude")
    a_records = []
    map_df = df[["latitude", "longitude"]].copy()
    for key, row in map_df.iterrows():
        a_records.append({key: row[key] for key in a_keys})

    for record in a_records:
        record["latitude"] = float(record["latitude"])
        record["longitude"] = float(record["longitude"])

    if is_gcm != "Y":
        map = folium.Map(
            location=[-34.01453443432472, 18.888931274414066], zoom_start=10
        )

        mCluster = MarkerCluster(name="Marker Cluster Test").add_to(map)

        for pnt in a_records:
            folium.Marker(location=[pnt["latitude"], pnt["longitude"]]).add_to(mCluster)

        # Main Markers
        folium.Marker(
            location=[-33.835463995969, 18.743258499887],
            popup="Orbit Commercial Vehicles Cape Town",
            icon=folium.Icon(color="green"),
        ).add_to(map)
        folium.Marker(
            location=[-33.634766192471, 19.466259040943],
            popup="Mercedes-Benz Worcester",
            icon=folium.Icon(color="green"),
        ).add_to(map)

        st_data = st_folium(map, width=1000)
    else:
        map = folium.Map(
            location=[-26.249698933197603, 28.166885375976566], zoom_start=10
        )

        mCluster = MarkerCluster(name="Marker Cluster Test").add_to(map)

        for pnt in a_records:
            folium.Marker(location=[pnt["latitude"], pnt["longitude"]]).add_to(mCluster)

        # Main Markers
        folium.Marker(
            location=[-25.978329985392, 28.118513090591],
            popup="Mercedes-Benz Grand Central Motors",
            icon=folium.Icon(color="green"),
        ).add_to(map)

        st_data = st_folium(map, width=1000)


@st.cache_data
def convert_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


if selected == "Orbit Active Customers":
    df = get_data("OA")
    df_selection = side_filter_selection(df)

    metrics(df_selection)
    veiw_filter = st.radio(label="Filter between Views", options=["Table", "Map"])
    if veiw_filter == "Table":
        table(df_selection)
    else:
        map_data(df_selection)

    csv = convert_to_csv(df_selection)

    download1 = st.download_button(
        label="Download Results",
        data=csv,
        file_name=f"ret-download-{today}.csv",
        mime="text/csv",
    )
elif selected == "Orbit Inactive Customers":
    df = get_data("OI")
    df_selection = side_filter_selection(df)
    metrics(df_selection)
    veiw_filter = st.radio(label="Filter between Views", options=["Table", "Map"])
    if veiw_filter == "Table":
        table(df_selection)
    else:
        map_data(df_selection)

    csv = convert_to_csv(df_selection)

    download1 = st.download_button(
        label="Download Results",
        data=csv,
        file_name=f"ret-download-{today}.csv",
        mime="text/csv",
    )
