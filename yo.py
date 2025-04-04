import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc

def data_process(x):
    
    all_row = x[x["Trader Name"]=="All"]
    clean_row = x[~x["Trader Name"].isin(["All","Unassigned"])]
    
    col = x.columns
    first_col = ["Executed Tickets","Executed Volume (M)","Attempted Tickets","Attempted Volume (M)"]
    new_col = ["Executed Tickets %","Executed Volume %","Attempted Tickets %","Attempted Volume %"]
    value = clean_row[first_col]/all_row[first_col].values*100
    
    clean_row[new_col] = value.apply(lambda x: round(x,2))
    clean_row =  clean_row.fillna(0)
    
    
    output = clean_row.loc()[:,clean_row.columns[2:]]
    output.index = clean_row.loc()[:,"Trader Name"]
    
    output.replace("N.A.", 0, inplace=True)
    return output
    

st.title("Desk viewer")

if "dataframe" not in st.session_state:
    st.session_state.dataframe = None

if "dataframe_cleaned" not in st.session_state:
    st.session_state.dataframe_cleaned = None
    
if "file" not in st.session_state:
    st.session_state.file = None

if "validated" not in st.session_state:
    st.session_state.validated = False

if "select" not in st.session_state:
    st.session_state.select = False


# File uploader only shown if file hasn't been selected yet or hasn't been validated
if st.session_state.file is None or not st.session_state.validated:
    st.session_state.file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx", "xls"])

if st.session_state.file is not None and not st.session_state.validated:
    
    df = pd.read_excel(st.session_state.file)
    st.write("Preview: ")
    st.dataframe(df)
    if st.button("Validate"):
        # Mark as validated when the button is clicked
        st.session_state.validated = True
        st.session_state.dataframe = df
        st.rerun()  # Use rerun to refresh the app state

# After validation, show the selectbox
if st.session_state.validated:
    st.session_state.select = True
    
    if st.session_state.dataframe_cleaned is None:
        
        df = st.session_state.dataframe
        st.session_state.total_client =  df[df["Trader Name"]=="All"].iloc()[1:]
        st.session_state.total_client.index = st.session_state.total_client["Customer Firm Name"]
        st.session_state.total_client = st.session_state.total_client.loc()[:,["Executed Tickets","Executed Volume (M)","Attempted Tickets","Attempted Volume (M)"]]
                                                                            
        group = df.groupby("Customer Firm Name")
        st.session_state.dataframe_cleaned = group.apply(data_process)
        print("dataframe_done")
        st.session_state.client = set(st.session_state.dataframe_cleaned.index.get_level_values(0))
        st.session_state.sales = set(st.session_state.dataframe_cleaned.swaplevel(0, 1).index.get_level_values(0))
    
    selected_rep = st.selectbox("View:", ["Client table", "Sales table"])

    # Add additional logic to display the selected data if needed
    # e.g. display the selected table
    if selected_rep == "Client table":
        
        df = st.session_state.dataframe_cleaned
        
        col_of_interest = ['Executed Tickets', 'Executed Volume (M)', 'Attempted Tickets','Attempted Volume (M)', 'Percentage Hit Ratio Tickets','Percentage Hit Ratio Volume']
        
        col_participation = ["Executed Tickets %","Executed Volume %","Attempted Tickets %","Attempted Volume %"]
        
        col1, col2 = st.columns([50,50])
        
        
        with col1:
                       
            st.subheader("Client")
            selected_clients = st.multiselect("Choisissez des noms :", options=sorted(st.session_state.client))
              
        with col2:
            
            st.subheader("Sales")
            selected_names = st.multiselect("Choisissez des noms :", options=sorted(st.session_state.sales))            
               
        df = st.session_state.dataframe_cleaned
        col_interest = ['Executed Tickets', 'Executed Volume (M)', 'Attempted Tickets', 'Attempted Volume (M)']
        
        index = pd.MultiIndex.from_product([selected_clients, selected_names], names=["Client", "Sales"])
        df_ = pd.DataFrame(0, index=index, columns=df.columns)
        
        try:
            idx = pd.IndexSlice[selected_clients,selected_names]
            subset = df.loc[idx, :]
            df_.update(subset)
        except:
            pass
        
        #st.dataframe(df_)
        
        graph = st.selectbox("Graph", col_interest)
        st.dataframe(df_)
        set_colors = pc.qualitative.Safe
        color_map = {sales: set_colors[i % len(set_colors)] for i, sales in enumerate(selected_names)}
        
        try:
            df_unstacked = df_[graph].unstack(fill_value=0)
        except:
            df_unstacked =pd.DataFrame([],index=index, columns=df.columns)
                    
        fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                            subplot_titles=("Per Sales (stacked)", "Total Client"))
        
        fig_prop = go.Figure()
        totals = df[graph].unstack(fill_value=0).sum(1)[selected_clients]
        
        # Pour chaque client : stack manuellement ses sales dans l’ordre décroissant
        for client in df_unstacked.index:
            # Trier les sales de ce client localement
            sorted_sales = df_unstacked.loc[client].sort_values(ascending=False)

            for i, (sales, value) in enumerate(sorted_sales.items()):
                
                fig.add_trace(go.Bar(
                    name=sales+" "+client, #if client == df_unstacked.index[0] else None,  # éviter légende répétée
                    x=[client],
                    y=[value],
                    marker_color=color_map.get(sales, "#888"),
                    
                    
                ), row=1, col=1)
                #showlegend=(client == df_unstacked.index[0]),

                fig_prop.add_bar(
                                name=sales+" "+client, #if client == df_unstacked.index[0] else None,  # éviter légende répétée
                                x=[client],
                                y=[value/totals[client]*100],
                                
                                marker_color=color_map.get(sales, "#888"),
                                
                            )
                #showlegend=(client == df_unstacked.index[0]),
                
                
        

        fig.add_trace(go.Bar(
            name="Total Client",
            x=totals[df_unstacked.index].index,
            y=totals[df_unstacked.index].values,
            marker_color="#1f77b4"
        ), row=1, col=2)                
                
                

        fig_prop.update_layout(
            barmode='stack',
            title_text=f"Participation of {graph} in %",
            height=600,
            xaxis_tickangle=-45
        ) 
        
        
        fig.update_layout(
            barmode='stack',
            title_text=f"Sales vs Total of {graph} per client",
            height=600,
            xaxis_tickangle=-45
        ) 
        
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(fig_prop, use_container_width=True)

    elif selected_rep == "Sales table":
        
        df = st.session_state.dataframe_cleaned.swaplevel(0, 1).sort_index()
        col_of_interest = ['Executed Tickets', 'Executed Volume (M)', 'Attempted Tickets',
       'Attempted Volume (M)']
        selected_rep = st.selectbox("Choose a sales :", sorted(st.session_state.sales))      
        selected = df.loc()[selected_rep,col_of_interest]
        st.dataframe(selected)
        
        graph = st.selectbox("View:", col_of_interest)

        column_name = graph
        scope = df.loc()[selected_rep,column_name].sort_values(ascending=False).iloc()[:10]
        tot = st.session_state.total_client.loc()[scope.index,column_name]
        fig = go.Figure(data=[go.Bar(name=f"Sales {selected_rep}", x=scope.index, y=scope.values, marker_color='skyblue'),
                              go.Bar(name="Total Client", x=tot.index, y=tot.values, marker_color='crimson')])
        fig.update_layout(xaxis_tickangle=-45)  # Incline les labels
        fig.update_layout(barmode='group',title=f"Top Clients - Sales {selected_rep} vs Total",xaxis_title="Client",
                          yaxis_title=column_name,xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
