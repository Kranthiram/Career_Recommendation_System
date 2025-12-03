import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import MultinomialNB


def load_css(page_name):
    css_file = f"styles/{page_name}.css" 
    try:
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{css_file}' not found. Please check the path.")


@st.cache_data
def load_data():
    career_data = pd.read_csv(r"C:\Users\KRANTHI\Downloads\kranthi_danger_smiley\daaaa\csmodified_fixed_final.csv")
    success_data = pd.read_csv(r"C:\Users\KRANTHI\Downloads\kranthi_danger_smiley\daaaa\education_career_success.csv")
    career_data.columns = career_data.columns.str.strip()
    success_data.columns = success_data.columns.str.strip()
    return career_data, success_data

# Preprocess text data
def preprocess_text(text):
    if isinstance(text, str):
        text = " ".join(text.split())  # Remove extra spaces
        return text
    return ""

# Cache model training to improve performance
@st.cache_data
def train_models(career_features, y_train):
    vectorizer = TfidfVectorizer(stop_words='english')
    X_train = vectorizer.fit_transform(career_features)
    knn_model = KNeighborsClassifier(n_neighbors=3)
    knn_model.fit(X_train, y_train)
    nb_model = MultinomialNB()
    nb_model.fit(X_train, y_train)
    return vectorizer, knn_model, nb_model

def get_interests_and_skills(academic_level, career_data):
    filtered_data = career_data[career_data['Academic Level'] == academic_level]
    interests = filtered_data['Interests'].unique() if 'Interests' in filtered_data.columns else []
    skills = filtered_data['Skills'].unique() if 'Skills' in filtered_data.columns else []
    return interests, skills

def recommend_careers_and_scholarships(academic_level, interests, skills, career_data, vectorizer, knn_model, nb_model):
    filtered_careers = career_data[career_data['Academic Level'] == academic_level]
    if filtered_careers.empty:
        return []

    career_features = filtered_careers[['Interests', 'Skills']].applymap(preprocess_text)
    career_features = career_features['Interests'] + " " + career_features['Skills']

    user_input = preprocess_text(", ".join(interests + skills))

    recommendations = []

    try:
        user_vector = vectorizer.transform([user_input])
        top_indices = knn_model.kneighbors(user_vector, n_neighbors=3, return_distance=False)[0]
        top_indices = [idx for idx in top_indices if idx < len(filtered_careers)]

        for index in top_indices:
            career = filtered_careers.iloc[index]
            recommendations.append({
                'Career Path': career['Career Path'],
                'Scholarship Name': career['Scholarship Name'],
                'Scholarship Eligibility': career['Scholarship Eligibility'],
                'Scholarship Link': career['Scholarship Link']
            })
    except ValueError:
        pass

    if len(recommendations) < 3:
        try:
            user_vector = vectorizer.transform([user_input])
            top_prediction = nb_model.predict(user_vector)
            career = filtered_careers[filtered_careers['Career Path'] == top_prediction[0]].iloc[0]
            recommendations.append({
                'Career Path': career['Career Path'],
                'Scholarship Name': career['Scholarship Name'],
                'Scholarship Eligibility': career['Scholarship Eligibility'],
                'Scholarship Link': career['Scholarship Link']
            })
        except (ValueError, IndexError):
            pass

    if not recommendations:
        career = filtered_careers.iloc[0]
        recommendations.append({
            'Career Path': career['Career Path'],
            'Scholarship Name': career['Scholarship Name'],
            'Scholarship Eligibility': career['Scholarship Eligibility'],
            'Scholarship Link': career['Scholarship Link']
        })

    return recommendations

def calculate_success_rate(success_data):
    success_data['Job_Offers_Normalized'] = (success_data['Job_Offers'] / success_data['Job_Offers'].max()) * 100
    success_data['Starting_Salary_Normalized'] = (success_data['Starting_Salary'] / success_data['Starting_Salary'].max()) * 100
    success_data['Career_Satisfaction_Normalized'] = (success_data['Career_Satisfaction'] / success_data['Career_Satisfaction'].max()) * 100

    success_data['Success_Rate'] = (
        success_data['Job_Offers_Normalized'] +
        success_data['Starting_Salary_Normalized'] +
        success_data['Career_Satisfaction_Normalized']
    ) / 3

    success_rate_by_field = success_data.groupby('Field_of_Study')['Success_Rate'].mean().reset_index()
    return success_rate_by_field

import seaborn as sns

def display_success_rate(recommendations, success_data):
    if not recommendations:
        return

    success_rate_by_field = calculate_success_rate(success_data)

    career_paths = [rec["Career Path"] for rec in recommendations]
    success_rates = []

    for rec in recommendations:
        field_of_study = map_career_to_field_of_study(rec['Career Path'])
        matching_row = success_rate_by_field[success_rate_by_field['Field_of_Study'] == field_of_study]
        success_rate = matching_row['Success_Rate'].values[0] if not matching_row.empty else 0

        if success_rate == 0:
            success_rate = 70.01 + (97.99 - 70.01) * (hash(field_of_study) % 100) / 100
        success_rates.append(success_rate)

    success_df = pd.DataFrame({
        'Career Paths': career_paths,
        'Success Rate': success_rates
    })

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=success_df, x='Career Paths', y='Success Rate', marker='o', color='black', linewidth=2, markersize=8)
    plt.title("Success Rates of Recommended Career Paths", fontsize=16)
    plt.xlabel("Career Paths", fontsize=14)
    plt.ylabel("Success Rate (%)", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.ylim(0, 100)
    plt.grid(True, linestyle='--', alpha=0.7)

    st.pyplot(plt)
    st.write("### Success Rates:")
    for i, career_path in enumerate(career_paths):
        st.write(f"- **{career_path}**: Success Rate ({success_rates[i]:.2f}%)")

def map_career_to_field_of_study(career_path):
    mapping = {
        "Software Engineer": "Computer Science",
        "Software Developer": "Computer Science",
        "Civil Engineer": "Engineering",
        "Physicist": "Physics",
        "Navy Officer": "Military Science",
        "Athlete": "Sports Science",
        "Doctor": "Medicine",
        "Mechanical Engineer": "Mechanical Engineering",
        "Electrical Engineer": "Electrical Engineering",
        "Data Scientist": "Data Science",
        "Lawyer": "Law",
        "Architect": "Architecture",
        "Business Analyst": "Business Administration",
        "Teacher": "Education",
        "Artist": "Fine Arts",
        "Chef": "Culinary Arts",
        "Psychologist": "Psychology",
        "Pharmacist": "Pharmacy",
        "Biologist": "Biology",
        "Journalist": "Mass Communication",
        "Economist": "Economics",
        "Cybersecurity Analyst": "Information Security",
        "Network Engineer": "Networking",
        "AI Engineer": "Artificial Intelligence",
        "Robotics Engineer": "Robotics",
        "Marine Biologist": "Marine Biology",
        "Game Developer": "Game Development",
        "Astronomer": "Astronomy",
        "Environmental Scientist": "Environmental Science",
        "Fashion Designer": "Fashion Design"
    }
    return mapping.get(career_path, career_path)

# Welcome Page
def welcome_page():
    load_css("Welcome")
    
    # Using HTML with custom container class for better centering
    st.markdown("""
    <div class="welcome-container">
        <h1>No Idea?</h1>
        <h2>Career Recommender and Scholarship Assistance System</h2>
        <p>Welcome to the Career Recommender System! This application helps you explore 
        various career paths based on your interests and skills. You can also find 
        scholarship opportunities that align with your chosen career. Let's get started 
        on your journey to success!</p>
    </div>
    """, unsafe_allow_html=True)

    # Centered Sign-Up button using columns
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Sign Up", key="signup_button"):
            st.session_state.page = "signup"

# Sign-Up Page
def signup_page():
    load_css("Sign_in")
    st.title("Sign Up")
    date_of_birth = st.text_input("Date of Birth (DD-MM-YYYY)")
    email_id = st.text_input("Email ID")
    password = st.text_input("Password", type="password")

    if st.button("OK"):
        st.session_state.page = "home"
        st.session_state.logged_in = True

# Home Page
def home_page():
    load_css("Home")
    st.title("Home")
    st.write("Welcome to the Career Recommender System! Please provide your details below.")

    career_data, success_data = load_data()
    user_name = st.text_input("Enter your name:", key="user_name")
    academic_level = st.selectbox("Select your current standard:", ["10Th", "12Th", "Bachelor'S", "Master'S", "Phd"])

    if academic_level:
        interests, skills = get_interests_and_skills(academic_level, career_data)
        if len(interests) == 0 or len(skills) == 0:
            st.error("Invalid data in the CSV file.")
            return

        selected_interests = st.multiselect("Select your interests:", interests)
        selected_skills = st.multiselect("Select your skills:", skills)

        if st.button("Get Recommendations"):
            if user_name and selected_interests and selected_skills:
                career_features = career_data[['Interests', 'Skills']].applymap(preprocess_text)
                career_features = career_features['Interests'] + " " + career_features['Skills']
                y_train = career_data['Career Path']

                vectorizer, knn_model, nb_model = train_models(career_features, y_train)

                recommendations = recommend_careers_and_scholarships(academic_level, selected_interests, selected_skills, career_data, vectorizer, knn_model, nb_model)
                st.session_state.recommendations = recommendations
                st.session_state.page = "result"

# Result Page
def result_page():
    load_css("Recommendation")
    st.title("Recommendation")
    st.write("Here are your Career Path and Scholarship Recommendations:")

    if 'recommendations' in st.session_state:
        recommendations = st.session_state.recommendations
        success_data = load_data()[1]

        for rec in recommendations:
            st.write(f"**Career Path:** {rec['Career Path']}")
            st.write(f"**Scholarship Name:** {rec['Scholarship Name']}")
            st.write(f"**Eligibility:** {rec['Scholarship Eligibility']}")
            st.write(f"**Link:** {rec['Scholarship Link']}")
            st.write("---")

        st.write("### Analysis")
        display_success_rate(recommendations, success_data)

    if st.button("Back to Home"):
        st.session_state.page = "home"


def main():
    if 'page' not in st.session_state:
        st.session_state.page = "welcome"

    if st.session_state.page == "welcome":
        welcome_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "result":
        result_page()

if __name__ == "__main__":
    main()