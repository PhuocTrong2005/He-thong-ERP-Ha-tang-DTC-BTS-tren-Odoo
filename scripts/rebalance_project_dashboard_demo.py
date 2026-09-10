"""Rebalance ANL project states and deadlines for a varied project dashboard."""

from datetime import date, timedelta


TODAY = date.today()
PREFIX = "ANL-DA-"
CONTEXT = {
    "tracking_disable": True,
    "mail_notrack": True,
    "mail_create_nosubscribe": True,
    "mail_auto_subscribe_no_notify": True,
    "bts_skip_workflow_email": True,
}

Project = env["project.project"].sudo().with_context(**CONTEXT)
projects = Project.search(
    [("project_code", "=like", f"{PREFIX}%")],
    order="project_code",
)
if len(projects) != 30:
    raise AssertionError(f"Expected 30 ANL projects, found {len(projects)}")

# Eight completed projects: four on time and four late, distributed over
# recent months so the monthly completion chart contains both series.
completed_delays = (-18, -7, 0, -3, 8, 19, 37, 64)
for index, project in enumerate(projects[:8]):
    acceptance = project.acceptance_date
    if not acceptance:
        raise AssertionError(f"{project.project_code} has no acceptance date")
    planned_end = acceptance - timedelta(days=completed_delays[index])
    project.write({
        "state": "done",
        "planned_start_date": planned_end - timedelta(days=150),
        "planned_end_date": planned_end,
    })

# Active portfolio: future deadlines beyond 30 days are on time; deadlines in
# the next 30 days are at risk; past deadlines are late.
active_specs = [
    ("in_progress", -95),
    ("in_progress", -42),
    ("in_progress", -12),
    ("in_progress", 5),
    ("in_progress", 16),
    ("in_progress", 45),
    ("in_progress", 110),
    ("approved", -70),
    ("approved", -8),
    ("approved", 9),
    ("approved", 27),
    ("approved", 80),
    ("survey", -25),
    ("survey", 20),
    ("survey", 135),
]
for project, (state, deadline_offset) in zip(projects[8:23], active_specs):
    planned_end = TODAY + timedelta(days=deadline_offset)
    project.write({
        "state": state,
        "planned_start_date": planned_end - timedelta(days=135),
        "planned_end_date": planned_end,
    })

# Two cancelled projects remain visible in the status donut but are excluded
# from progress-delay metrics by dashboard rules.
for offset, project in enumerate(projects[23:25], start=1):
    project.write({
        "state": "cancelled",
        "planned_start_date": TODAY - timedelta(days=180 + offset * 15),
        "planned_end_date": TODAY - timedelta(days=30 + offset * 20),
    })

# Five draft projects: one station each and intentionally no downstream data.
for offset, project in enumerate(projects[25:30], start=1):
    project.write({
        "state": "draft",
        "planned_start_date": TODAY + timedelta(days=60 + offset * 30),
        "planned_end_date": TODAY + timedelta(days=210 + offset * 30),
        "acceptance_date": False,
    })

expected_states = {
    "done": 8,
    "in_progress": 7,
    "approved": 5,
    "survey": 3,
    "cancelled": 2,
    "draft": 5,
}
actual_states = {
    state: len(projects.filtered(lambda project, state=state: project.state == state))
    for state in expected_states
}
assert actual_states == expected_states, (actual_states, expected_states)

env.cr.commit()
print("PROJECT_DASHBOARD_REBALANCE_OK")
print("State totals:", actual_states)
