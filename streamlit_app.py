# streamlit_app.py

import streamlit as st
from Bio import Entrez
from datetime import datetime, timedelta
import pandas as pd

# Set your email for NCBI access
Entrez.email = "your_email@example.com"  # 🔁 Replace with your email

# ---- Sidebar Inputs ----
st.sidebar.title("Faculty Publication Search")
faculty_input = st.sidebar.text_area("Enter faculty names (one per line):", height=150)
days_back = st.sidebar.number_input("Number of days to look back:", min_value=1, value=60)

if st.sidebar.button("Search PubMed"):
    faculty_list = [name.strip() for name in faculty_input.splitlines() if name.strip()]
    start_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    end_date = datetime.today().strftime("%Y/%m/%d")

    all_results = []

    def search_pubmed(author_name):
        search_query = (
            f"{author_name}[Author] AND University of Miami[Affiliation] "
            f"AND (\"{start_date}\"[PDAT] : \"{end_date}\"[PDAT])"
        )
        handle = Entrez.esearch(db="pubmed", term=search_query, retmax=100)
        search_results = Entrez.read(handle)
        handle.close()
        return search_results['IdList']

    def fetch_details(id_list):
        ids = ",".join(id_list)
        handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        return records

    def format_citation(article):
        authors = article['MedlineCitation']['Article'].get('AuthorList', [])
        author_names = []
        for author in authors:
            if 'LastName' in author and 'Initials' in author:
                author_names.append(f"{author['LastName']} {author['Initials']}.")
        author_string = ", ".join(author_names)

        title = article['MedlineCitation']['Article']['ArticleTitle']
        journal = article['MedlineCitation']['Article']['Journal']['Title']
        pub_date = article['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']

        year = pub_date.get('Year', 'n.d.')
        month = pub_date.get('Month', '')
        day = pub_date.get('Day', '')

        volume = article['MedlineCitation']['Article']['Journal']['JournalIssue'].get('Volume', '')
        issue = article['MedlineCitation']['Article']['Journal']['JournalIssue'].get('Issue', '')
        pagination = article['MedlineCitation']['Article'].get('Pagination', {}).get('MedlinePgn', '')

        doi = None
        for id_tag in article['PubmedData']['ArticleIdList']:
            if id_tag.attributes['IdType'] == 'doi':
                doi = id_tag

        citation = f"{author_string}. {title} {journal}. {year} {month} {day}; {volume}"
        if issue:
            citation += f"({issue})"
        if pagination:
            citation += f":{pagination}."
        else:
            citation += "."
        if doi:
            citation += f" doi: {doi}"
        return citation

    for faculty in faculty_list:
        st.markdown(f"### 🔍 {faculty}")
        pubmed_ids = search_pubmed(faculty)
        if pubmed_ids:
            records = fetch_details(pubmed_ids)
            for article in records['PubmedArticle']:
                citation = format_citation(article)
                st.markdown(f"- {citation}")
                all_results.append({"Faculty": faculty, "Citation": citation})
        else:
            st.markdown("*No publications found.*")
            all_results.append({"Faculty": faculty, "Citation": "No publications found."})

    # Show results as a table + option to download
    if all_results:
        df = pd.DataFrame(all_results)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download as CSV", data=csv, file_name="faculty_publications.csv", mime="text/csv")
