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
  - The date the workout was performed (date picker, defaults to today)
  - The time of each interval (entered sequentially in order: interval 1, 2, 3, etc.)
- A landing page that lets the user navigate to the above pages.

## Non Functional requirements

- Backend: Python/Django
- Frontend: Typescript/React
- Keep this as simple as possible while meeting all requirements in this spec.
- We only need to run in dev mode on localhost.
- Single-user application with no authentication required.
- No edit capability for now; users can only create and delete records.
- Delete operations require confirmation dialogs.

## Time Format

- **Display**: `m:ss` for times under 1 hour (e.g., "1:45"), `h:mm:ss` for times of 1 hour or more (e.g., "1:02:30")
- **Entry**: Single text field requiring colon format. Accepted formats: `m:ss`, `mm:ss`, or `h:mm:ss`

## Empty States

- No workout structures: "No workout structures defined yet. Create one to get started."
- No performed workouts: "No workouts recorded yet. Record your first workout!"
- Creating a performed workout when no structures exist: Disable the form with a message prompting the user to create a structure first.

