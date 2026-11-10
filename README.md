# TheMove
### What's the Move?
**Good Plans. Better Memories.**

**Machine Learning Final Project | Fall 2026**

**Team Members:** Ola Oluwa James-Owolabi and Emmanuella Turkson

## 1. Project Overview

Have you ever spent an hour in a group chat trying to decide where to go, only for everyone to end up staying home?

TheMove is a group activity recommendation project designed to address that problem.

The project explores how machine learning and group preference aggregation can support decisions when friends have different interests, budgets, and expectations.

Our long-term goal is to create an application where friends can enter their preferences and receive three activity suggestions, with one highlighted as the best recommendation for the group.

The current prototype demonstrates group preference matching and location-based activity discovery in Little Rock, Arkansas.

## 2. Problem Statement

Making plans with a group can be challenging because everyone has different preferences and financial limitations.

Traditional recommendation systems often focus on individuals rather than groups.

TheMove investigates how individual preferences can be combined to recommend activities that consider the interests of multiple people.

Our research focuses on two questions:

1. How accurately can different machine learning approaches predict individual activity preferences?
2. How effectively can these predictions support group recommendations?

## 3. Project Objectives

- Explore group recommendation and preference prediction techniques.
- Compare a popularity-based baseline, Random Forest, and collaborative filtering using KNN.
- Evaluate recommendation performance on unseen groups.
- Investigate average-satisfaction and minimum-satisfaction recommendation strategies.
- Develop a location-based prototype using real geographic venue data.
- Explore conversational interaction for refining group recommendations.

## 4. Datasets

### Group Decision-Making Dataset

The primary machine learning dataset contains:

- 2,772 individual rating records.
- 282 participant profiles.
- 79 groups.
- Ratings for 10 anonymous items, labeled D1–D10.
- Recorded group choices and group composition information.

This dataset supports individual preference prediction and group recommendation experiments.

### Restaurant & Consumer Dataset

An additional dataset includes:

- Restaurant information.
- User profiles.
- Restaurant ratings.
- Food and service ratings.

This dataset was explored as a supplementary source of information.

### OpenStreetMap Geographic Data

OpenStreetMap-derived geographic data was used to develop the location-based prototype.

The processed Little Rock catalog contains 261 named venues, including restaurants, cafés, parks, cultural attractions, and recreation locations.

The catalog includes venue names, activity categories, coordinates, and approximate distances from downtown Little Rock.

It does not contain verified prices or current opening hours.

## 5. Machine Learning Methodology

### Popularity Baseline

The popularity baseline uses average item ratings from the training dataset to predict user preferences.

It provides a simple reference point for evaluating more complex approaches.

### Random Forest

A Random Forest regression pipeline was trained using item identifiers and selected participant features.

The model uses features including:

- Item
- Openness
- Conscientiousness
- Extraversion
- Agreeableness
- Emotional stability
- Experience

### Collaborative Filtering (KNN)

User-based KNN identifies similar users using their rating patterns.

A warm-start experiment evaluates predictions after each validation user reveals three initial ratings.

### Group Recommendation Strategies

Two strategies were examined:

**Average Satisfaction:** Selects the activity with the highest average predicted rating across group members.

**Minimum Satisfaction:** Selects the activity with the highest lowest-member predicted rating, aiming to reduce the chance that one member is strongly dissatisfied.

## 6. Model Evaluation

The data was divided into group-aware training, validation, and testing partitions.

- Training groups: 55
- Validation groups: 12
- Testing groups: 12

No users overlapped between these partitions.

### Warm-Start Rating Prediction - Validation

| Model | MAE | RMSE |
|---|---:|---:|
| Popularity Baseline | 2.4367 | 2.8230 |
| Random Forest | 2.5000 | 2.9045 |
| User-Based KNN | **2.3036** | **2.7371** |

KNN achieved the lowest reported prediction error in the warm-start validation experiment.

### Group Recommendation Accuracy

| Recommendation Method | Validation | Test |
|---|---:|---:|
| Popularity Baseline | 25.00% | **41.67%** |
| Random Forest - Average | 25.00% | 25.00% |
| Random Forest - Minimum | **41.67%** | 25.00% |

Each evaluation partition contained 12 groups.

Although Random Forest with minimum satisfaction performed best during validation, the popularity baseline achieved the highest match rate on the held-out group test.

These findings should be interpreted cautiously because of the small evaluation sample.

The KNN warm-start rating experiment and group-choice evaluation measure different outcomes and are not directly interchangeable.

## 7. Streamlit Application

TheMove includes a Streamlit prototype with a mango-inspired visual identity.

### Current Features

- Group planning for two to five friends.
- Individual budget inputs.
- Individual mood and activity preferences.
- Activity category ranking based on group inputs.
- Discovery of named Little Rock venues.
- Interactive location map.
- Explanations of the current rule-based matching approach.
- Warnings about unavailable price information.

The local venue-ranking prototype uses explicit activity selections, keyword matching, and geographic filtering.

**Important:** The trained research models predict ratings for anonymous dataset items (D1–D10). They have not been trained to predict ratings for individual Little Rock venues.

The local prototype should therefore not be interpreted as a deployment of the evaluated Random Forest or KNN models.

## 8. Running the Project

### Machine Learning Notebook

1. Download or clone this repository.
2. Open `TheMove_Final_Project.ipynb` in Google Colab.
3. Upload the required Group Decision-Making dataset files.
4. Run the notebook cells in order.
5. Review the model evaluation tables and charts.

The optional geographic processing step can reuse the existing processed venue CSV.

### Streamlit Application

Install the application dependencies:

```bash
pip install -r TheMove_Frontend/requirements.txt
```

Run the application:

```bash
streamlit run TheMove_Frontend/app.py
```

The venue CSV and logo assets must be available inside the `TheMove_Frontend` folder.

## 9. AI Features and Testing

TheMove's planned conversational feature will allow users to ask questions about recommendations and refine their preferences.

Examples include:

- Why was this activity recommended?
- Can we find something cheaper?
- What if someone prefers outdoor activities?
- Can we try another suggestion?

A twelve-case testing plan was developed to assess preferences, budget constraints, conflicting interests, location restrictions, and explanations.

The current application primarily uses rule-based responses and matching. A fully integrated generative conversational assistant has not yet been verified.

## 10. Limitations

The project has several limitations:

- The primary research dataset is relatively small.
- Only 12 groups were included in each final evaluation partition.
- The research dataset contains anonymous destination identifiers rather than named local venues.
- The processed venue catalog is restricted to the Little Rock area.
- Venue prices, operating hours, and availability are not verified.
- The local venue catalog is imbalanced across activity categories.
- The Streamlit recommendation interface is not yet connected to the trained research models.
- The conversational AI capability remains under development.

These limitations inform future development and prevent unsupported claims about recommendation accuracy.

## 11. Future Improvements

Future development could include:

- Dynamic OpenStreetMap searches for additional cities.
- Reliable venue pricing and operating-hour information.
- A trained local activity preference model.
- Better handling of individual budget constraints.
- Conversational recommendation refinement.
- Three personalized suggestions with one highlighted recommendation.
- Verified venue website links and navigation.
- Larger-scale testing with real users and groups.

## 12. Technologies Used

- Python
- Pandas
- NumPy
- Scikit-learn
- Google Colab
- Jupyter Notebook
- Streamlit
- GeoPandas
- OpenStreetMap geographic data
- GitHub

## 13. Team Members

**Ola Oluwa James-Owolabi**

**Emmanuella Turkson**

Detailed individual contributions are documented separately in the final project submission.

## 14. Conclusion

TheMove explores how machine learning can support group decision-making by predicting individual preferences and combining them into recommendations.

The experiments show that user-based KNN can improve rating prediction when initial preferences are available. However, the popularity baseline performed best on the held-out group-choice test.

The project also demonstrates a practical prototype for discovering local activities based on group interests.

Together, the machine learning experiments and Streamlit application provide a foundation for a more advanced location-aware group recommendation system.
