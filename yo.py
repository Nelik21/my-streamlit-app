import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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
            selected_clients = st.multiselect("Choisissez des noms :", options=st.session_state.client)
              
        with col2:
            
            st.subheader("Sales")
            selected_names = st.multiselect("Choisissez des noms :", options=st.session_state.sales)            
               
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
        
        st.dataframe(df_)
        
        graph = st.selectbox("Graph", col_interest)
    
        df_unstacked = df_[graph].unstack(fill_value=0)

        # Construction du graphique Plotly
        fig = go.Figure()

        for sales in df_unstacked.columns:
            fig.add_bar(
                name=sales,
                x=df_unstacked.index,
                y=df_unstacked[sales]
            )

        # Configuration de l’empilement
        fig.update_layout(
            barmode='stack',  # => bar chart empilé
            title="Tickets exécutés par Client et Sales",
            xaxis_title="Client",
            yaxis_title="Executed Tickets",
            legend_title="Sales",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)     

        
    elif selected_rep == "Sales table":
        
        df = st.session_state.dataframe_cleaned.swaplevel(0, 1).sort_index()
        col_of_interest = ['Executed Tickets', 'Executed Volume (M)', 'Attempted Tickets',
       'Attempted Volume (M)', 'Percentage Hit Ratio Tickets',
       'Percentage Hit Ratio Volume']
        selected_rep = st.selectbox("Choose a sales :", st.session_state.sales)      
        selected = df.loc()[selected_rep,col_of_interest]
        st.dataframe(selected)
        
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            
            st.subheader("🧩 Graphiques")
            executed_tickets = st.checkbox("Top Executed Tickets")
            executed_volume = st.checkbox("Top Executed Volume")
            attempted_tickets = st.checkbox("Top Attempted Tickets")
            attempted_volume = st.checkbox('Top Attempted Volume')

        
        with col1:
            st.subheader("📈 Visualisation")

            if executed_tickets:
                
                column_name = "Executed Tickets"
                scope = df.loc()[selected_rep,column_name].sort_values(ascending=False).iloc()[:10]
                tot = st.session_state.total_client.loc()[scope.index,column_name]
                fig = go.Figure(data=[go.Bar(name=f"Sales {selected_rep}", x=scope.index, y=scope.values, marker_color='skyblue'),
                                      go.Bar(name="Total Client", x=tot.index, y=tot.values, marker_color='crimson')])
                fig.update_layout(xaxis_tickangle=-45)  # Incline les labels
                fig.update_layout(barmode='group',title=f"Top Clients - Sales {selected_rep} vs Total",xaxis_title="Client",
                                  yaxis_title=column_name,xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                
                
            if executed_volume:
                
                column_name = 'Executed Volume (M)'
                scope = df.loc()[selected_rep,column_name].sort_values(ascending=False).iloc()[:10]
                tot = st.session_state.total_client.loc()[scope.index,column_name]
                fig = go.Figure(data=[go.Bar(name=f"Sales {selected_rep}", x=scope.index, y=scope.values, marker_color='skyblue'),
                                      go.Bar(name="Total Client", x=tot.index, y=tot.values, marker_color='crimson')])
                fig.update_layout(xaxis_tickangle=-45)  # Incline les labels
                fig.update_layout(barmode='group',title=f"Top Clients - Sales {selected_rep} vs Total",xaxis_title="Client",
                                  yaxis_title=column_name,xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                
                
            if attempted_tickets:
                
                column_name = 'Attempted Tickets'
                scope = df.loc()[selected_rep,column_name].sort_values(ascending=False).iloc()[:10]
                tot = st.session_state.total_client.loc()[scope.index,column_name]
                fig = go.Figure(data=[go.Bar(name=f"Sales {selected_rep}", x=scope.index, y=scope.values, marker_color='skyblue'),
                                      go.Bar(name="Total Client", x=tot.index, y=tot.values, marker_color='crimson')])
                fig.update_layout(xaxis_tickangle=-45)  # Incline les labels
                fig.update_layout(barmode='group',title=f"Top Clients - Sales {selected_rep} vs Total",xaxis_title="Client",
                                  yaxis_title=column_name,xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                
                
                
            if attempted_volume:
                
                column_name = 'Attempted Volume (M)'
                scope = df.loc()[selected_rep,column_name].sort_values(ascending=False).iloc()[:10]
                tot = st.session_state.total_client.loc()[scope.index,column_name]
                fig = go.Figure(data=[go.Bar(name=f"Sales {selected_rep}", x=scope.index, y=scope.values, marker_color='skyblue'),
                                      go.Bar(name="Total Client", x=tot.index, y=tot.values, marker_color='crimson')])
                fig.update_layout(xaxis_tickangle=-45)  # Incline les labels
                fig.update_layout(barmode='group',title=f"Top Clients - Sales {selected_rep} vs Total",xaxis_title="Client",
                                  yaxis_title=column_name,xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
