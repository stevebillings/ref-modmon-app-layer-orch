# Project requirements

We need to build a web application that lets a user (a) define one or more workout structures, and (b) enter the details of a workout (following one of those workout structures).

Each workout structure describes an interval workout performed on a Concept 2 rowing ergometer (or equivalent rowing ergometer).

## Functional requirements

- One page where the User can see all defined workout structues, and create a new one. A workout structure consists of:
  - The number of intervals
  - The length of each work phase in meters
  - The duration of each rest phase in minutes
- One page where the user can see all performed workouts already entered, and create/enter a new one. A performed workout consists of:
  - The workout structure (selected from a pulldown list)
  - The time (minutes:seconds) of each of the workout phases
- A landing page that lets the user navigate to the above pages.

## Non Functional requirements

- Backend: Python/Django
- Frontend: Typescript/React
- Keep this as simple as possible while meeting all requirements in this spec.
- We only need to run in dev mode on localhost.

