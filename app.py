# Importing Libraries

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import gspread
from plotly.subplots import make_subplots


# Setting page layout to wide

st.set_page_config(layout="wide")


# Importing From Google Sheets

creds = st.secrets["gcp_service_account"]
gc = gspread.service_account_from_dict(creds)
sh = gc.open_by_url(st.secrets["url"])
worksheet = sh.worksheet("Sheet1")

@st.cache(ttl=600)
def get_dataframe(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df 

df = get_dataframe(worksheet)


# Transforming Data

df["Date"] = pd.to_datetime(df["Date"])
df.sort_values("Date", inplace=True)
df['year'] = df["Date"].dt.year
df['month'] = df["Date"].dt.month


# Making Graphs

# Making states filter

list_states = df['state'].unique()
list_states = np.insert(list_states,0,"All")

with st.sidebar:
    filter = st.selectbox(
        'State',
        list_states)


if filter == "All":
    df = df
else:
    df = df[df['state'] == filter]


# Metrics
Complaints = df['Count of Complaints'].sum()

closed_complaints = df['company_response'].str.lower().str.contains('close').sum()


timely =  round((df[df['timely'] == 'Yes']['Count of Complaints'].count() / df['timely'].count() ) * 100, 2)
timely_formated = f"{timely:,.2f} %" 

progress_complaints = df[df['company_response'] == 'In progress']['Count of Complaints'].count()

# Barchart
bar_data = df.groupby('product')['product'].count().sort_values(ascending = False)
bar_data_categories = []
for i in range(len(bar_data.values)):
    temp_dict = {"name" : bar_data.index[i], "value" : bar_data.values[i]}
    bar_data_categories.append(temp_dict)

# Linechart
line_data = df.groupby("Date")['Count of Complaints'].count()

# PieChart
pie_data = df.groupby(['submitted_via'])['Count of Complaints'].count().sort_values(ascending = True)

# Treemap
tree_data = df.groupby(['issue', 'sub_issue'])['Count of Complaints'].count().sort_values(ascending = False)
tree_data = tree_data.reset_index()



# Making UI

with st.container():
    # Header and Subheader
    col1, col2 = st.columns((1,15))

    with col1.container():
        st.image("/Users/kazmi/Stuff/Karachi_ai/CDE/Streamlit/complain.png")

    with col2.container():
        st.header("Financial Consumer Complaints")


st.subheader(f"Displaying Data for {filter} State")


with st.container():

    col1, col2, col3, col4 = st.columns((4))

    with col1.container():
        st.metric("Total Complaints", Complaints, delta=None, delta_color="normal", help=None)

    with col2.container():
        st.metric("Closed Complaints", closed_complaints, delta=None, delta_color="normal", help=None)

    with col3.container():
        st.metric("Timely Responded Complaints", timely_formated, delta=None, delta_color="normal", help=None)

    with col4.container():
        st.metric("In Progress Complaints", progress_complaints, delta=None, delta_color="normal", help=None)




with st.container():

    col1, col2 = st.columns((1,1))

    with col1.container():
        def horizontal_bar_labels(categories):
            subplots = make_subplots(
                rows=len(categories),
                cols=1,
                subplot_titles=[x["name"] for x in categories],
                shared_xaxes=True,
                print_grid=False,
                vertical_spacing=(0.45 / len(categories)),
            )
            subplots['layout'].update(
                width=550,
                plot_bgcolor='rgba(0,0,0,0)',
            )

            # add bars for the categories
            for k, x in enumerate(categories):
                subplots.add_trace(dict(
                    type='bar',
                    orientation='h',
                    y=[x["name"]],
                    x=[x["value"]],
                    text=["{:,.0f}".format(x["value"])],
                    hoverinfo='text',
                    textposition='auto',
                    marker=dict(
                        colorscale='Bluered_r',
                    ),
                ), k+1, 1)

            # update the layout
            subplots['layout'].update(
                showlegend=False,
            )
            for x in subplots["layout"]['annotations']:
                x['x'] = 0
                x['xanchor'] = 'left'
                x['align'] = 'left'
                x['font'] = dict(
                    size=12,
                )

            # hide the axes
            for axis in subplots['layout']:
                if axis.startswith('yaxis') or axis.startswith('xaxis'):
                    subplots['layout'][axis]['visible'] = False

            # update the margins and size
            subplots['layout']['margin'] = {
                 'l': 10,
            #     'r': 0,
            #     't': 20,
            #     'b': 1,
            }

            return subplots

        figbar = horizontal_bar_labels(bar_data_categories)
        figbar.update_layout(
                  title_text="Products By Complaints")

        st.plotly_chart(figbar, use_container_width=True)

    with col2.container():
        figln = px.line(line_data, x = line_data.index, y = line_data.values, title= 'No. Of Complaints Yearly Trend',
                        labels=dict(y="Total No. Of Complaints", year="Year"),
                        template= 'plotly_dark', )
        st.plotly_chart(figln, use_container_width=True)       

with st.container():

    col1, col2 = st.columns((1,1))

    with col1.container():
        figpie = px.pie(pie_data, values=pie_data.values, names=pie_data.index, title='Submitted Via?',
                hole=.5, template= 'plotly_dark',)
        st.plotly_chart(figpie, use_container_width=True) 

    with col2.container():
        figtree = px.treemap(tree_data, path=['issue', 'sub_issue'], values='Count of Complaints',
                  color= 'Count of Complaints',
                  color_continuous_scale='plasma',
                  title = "Complaints by Issue and Sub-Issue"
                  )
        figtree.update_coloraxes(showscale=False)
        st.plotly_chart(figtree, use_container_width=True) 





# Footer

footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed with ❤ by <a style='display: block; text-align: center;' href="https://www.linkedin.com/in/syedumairhassankazmi/" target="_blank">Syed Umair Hassan Kazmi</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)
