# Adaptive Study Planner (StudyFlow)

A rule-based study planning system built with Python and FastAPI that helps students create structured study schedules, track progress, analyze performance, and receive actionable recommendations for improving study consistency.

---

## Overview

StudyFlow is designed to solve a common student problem: deciding what to study, when to study, and how to stay consistent.

The system generates study schedules from user-defined subjects, topics, exam dates, study hours, and difficulty levels. It continuously tracks progress and provides performance insights and rule-based recommendations to help students improve their study habits.

---

## Features

### Smart Plan Creation

* Create personalized study plans
* Add multiple subjects and topics
* Set difficulty levels
* Configure exam dates
* Define daily study hours
* Select study mode (Balanced or Focus)

### Schedule Generation

* Automatically allocates study sessions
* Prioritizes tasks based on urgency and difficulty
* Creates structured daily schedules

### Progress Tracking

* Mark tasks as completed
* Track completion rate
* Monitor pending tasks
* View daily study status

### Performance Analytics

* Completion rate monitoring
* Consistency tracking
* Pending task analysis
* Exam countdown tracking

### Rule-Based Recommendations

* Workload adjustment suggestions
* Subject-specific focus recommendations
* Consistency improvement guidance
* Productivity insights

### Revision Queue

* Identifies completed topics that should be revisited
* Supports spaced revision planning

---

## Tech Stack

### Backend

* Python
* FastAPI

### Frontend

* HTML
* CSS
* JavaScript

### Storage

* JSON-based data storage

---

## System Architecture

The application follows a modular architecture.

```text
Student
   │
   ▼
Web Interface
   │
   ▼
FastAPI Backend (api.py)
   │
   ├──────── Planner Module
   │
   ├──────── Tracker Module
   │
   ├──────── Analyzer Module
   │
   └──────── Recommender Module
                │
                ▼
         JSON Data Storage
```

Detailed architecture is available in:

* Architecture.pdf

---

## Project Structure

```text
Adaptive Study Planner
│
├── api.py
├── planner.py
├── tracker.py
├── analyzer.py
├── recommender.py
├── storage.py
├── studyflow.html
├── study_data.json
├── requirements.txt
├── Architecture.pdf
├── Screenshots/
└── README.md
```

---

## Screenshots

### Dashboard Overview

Shows overall study progress, completion metrics, pending tasks, and exam countdown.

---

### Plan Creation - Subject Configuration

Students can add subjects, topics, estimated study time, and difficulty levels.

---

### Plan Creation - Schedule Settings

Configure exam dates, daily study hours, and study mode preferences.

---

### Generated Schedule

Automatically generated study plan organized into study sessions.

---

### Performance Dashboard

Displays study performance metrics and progress analytics.

---

### Recommendations Engine

Provides rule-based suggestions to improve study effectiveness.

---

### Daily Completion View

Displays completed study sessions and revision recommendations.

---

## How It Works

1. User creates a study plan.
2. Planner module generates a schedule.
3. Tracker records completed tasks.
4. Analyzer evaluates progress and performance.
5. Recommender generates improvement suggestions.
6. Revision queue identifies topics for future review.

---

## Installation

### Clone Repository

```bash
git clone https://github.com/kartikey602-beep/adaptive-study-planner.git
cd adaptive-study-planner
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
uvicorn api:app --reload
```

### Open Application

```text
http://127.0.0.1:8000
```

---

## Future Enhancements

* User authentication
* Database integration
* Cloud deployment
* Study reminders and notifications
* AI-powered recommendation engine
* Mobile application support

---

## Learning Outcomes

This project provided practical experience in:

* Backend API development using FastAPI
* Modular software architecture
* Rule-based recommendation systems
* Data tracking and analytics
* Frontend and backend integration
* Software engineering design principles

---

## Author

Kartikey Singh

B.Tech Computer Science Engineering (AI & ML)

Inderprastha Engineering College
