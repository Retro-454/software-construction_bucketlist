// ==========================================
// GLOBAL HELPERS
// ==========================================



const $ = id => document.getElementById(id);

// Display success and error messages
const status = (message, kind = '') => {
    $('status').textContent = message;
    $('status').className = `status ${kind}`;
};


// ==========================================
// USER IDENTIFICATION
// ==========================================

function actorId() {

    const value = Number($('actorId').value);

    if (!Number.isInteger(value) || value < 1) {
        throw new Error('Enter a valid existing user ID.');
    }

    return String(value);
}


// ==========================================
// API COMMUNICATION
// ==========================================

async function api(path, method = 'GET', payload) {

    const headers = {
        'X-Actor-Id': actorId()
    };

    if (payload !== undefined) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(path, {
        method,
        headers,
        ...(payload !== undefined
            ? { body: JSON.stringify(payload) }
            : {})
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error(
            `Unexpected server response (${response.status})`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.error || `Request failed (${response.status})`
        );
    }

    return data;
}


// Handle errors from API operations
async function run(action, after) {

    try {

        const result = await action();

        if (after) {
            await after(result);
        }

        return result;

    } catch (err) {

        status(err.message, 'error');

        return null;
    }
}


// Validate IDs
function positiveId(value, label) {

    const n = Number(value);

    if (!Number.isInteger(n) || n < 1) {
        throw new Error(`Enter a valid ${label}.`);
    }

    return n;
}


// ==========================================
// CREATE BUCKET
// ==========================================

$('bucketForm').addEventListener('submit', e => {

    e.preventDefault();

    run(async () => {

        const res = await api(
            '/api/buckets',
            'POST',
            {
                bucket_name: $('bucketName').value.trim()
            }
        );

        $('bucketId').value = res.id;

        status(
            `Bucket created (ID ${res.id}). You're its leader.`,
            'success'
        );

    });
});


// ==========================================
// CREATE CATEGORY
// ==========================================

$('categoryForm').addEventListener('submit', e => {

    e.preventDefault();

    run(async () => {

        const res = await api(
            '/api/categories',
            'POST',
            {
                bucket_id: positiveId(
                    $('bucketId').value,
                    'bucket ID'
                ),

                category_name: $('categoryName').value.trim()
            }
        );

        $('categoryId').value = res.id;
        $('taskCategory').value = res.id;

        status(
            `Category created (ID ${res.id}).`,
            'success'
        );

        await loadTasks();

    });
});


// ==========================================
// CREATE TASK
// ==========================================

$('taskForm').addEventListener('submit', e => {

    e.preventDefault();

    run(async () => {

        const data = {

            category_id: positiveId(
                $('taskCategory').value,
                'category ID'
            ),

            task_name: $('taskName').value.trim()
        };

        // Optional description
        if ($('taskDescription').value.trim()) {
            data.task_description =
                $('taskDescription').value.trim();
        }

        // Optional due date
        if ($('taskDueDate').value) {
            data.due_date = $('taskDueDate').value;
        }

        // Optional urgency
        if ($('taskUrgency').value !== '') {
            data.urgency = Number($('taskUrgency').value);
        }

        // Send new task to Flask
        const res = await api(
            '/api/tasks',
            'POST',
            data
        );

        status(
            `Task created (ID ${res.id}).`,
            'success'
        );

        // Clear the form
        $('taskName').value = '';
        $('taskDescription').value = '';
        $('taskDueDate').value = '';
        $('taskUrgency').value = '';

        // Refresh task list if viewing this category
        if (String(data.category_id) === $('categoryId').value) {
            await loadTasks();
        }

    });
});


// ==========================================
// LOAD AND SORT TASKS
// ==========================================

$('loadTasks').addEventListener('click', () => {
    run(loadTasks);
});

$('sortBy').addEventListener('change', () => {

    if ($('categoryId').value) {
        run(loadTasks);
    }

});


async function loadTasks() {

    const id = positiveId(
        $('categoryId').value,
        'category ID'
    );

    const sort = $('sortBy').value;

    // Request tasks and progress simultaneously
    const [tasks, progress] = await Promise.all([

        api(
            `/api/categories/${id}/tasks?sort=${encodeURIComponent(sort)}`
        ),

        api(
            `/api/categories/${id}/progress`
        )

    ]);

    // Set the currently selected category
    $('taskCategory').value = id;

    // Display progress
    $('progress').textContent =
        `${progress.completed} of ${progress.total} tasks completed`;

    const container = $('tasks');

    // Clear previous tasks
    container.replaceChildren();

    // Handle empty categories
    if (!tasks.length) {

        const message = document.createElement('p');

        message.className = 'muted';

        message.textContent =
            'No tasks in this category yet.';

        container.append(message);
    }

    // Display each task
    for (const task of tasks) {
        container.append(renderTask(task));
    }

    status(
        `Loaded ${tasks.length} top-level task(s) from category ${id}.`,
        'success'
    );
}


// ==========================================
// RENDER TASKS
// ==========================================

function renderTask(task) {

    // Create task card
    const article = document.createElement('article');

    article.className =
        `task ${task.is_complete ? 'done' : ''}`;

    // Task title
    const title = document.createElement('div');

    title.className = 'task-title';
    title.textContent = task.task_name;

    // Completion badge
    const badge = document.createElement('span');

    badge.className = 'badge';

    badge.textContent =
        task.is_complete ? 'Complete' : 'Open';

    title.append(badge);
    article.append(title);


    // ======================================
    // TASK INFORMATION
    // ======================================

    const info = document.createElement('p');

    info.className = 'task-info';

    info.textContent =
        `Task #${task.task_id} · ` +
        `Due: ${task.due_date || 'None'} · ` +
        `Urgency: ${task.urgency ?? 'Unset'} · ` +
        `Assigned to: ${task.assignee_name || 'Unassigned'}`;

    article.append(info);


    // Task description
    if (task.task_description) {

        const desc = document.createElement('p');

        desc.textContent = task.task_description;

        article.append(desc);
    }


    // ======================================
    // DISPLAY NOTES
    // ======================================

    if (task.notes) {

        const notes = document.createElement('div');

        notes.className = 'notes';
        notes.textContent = task.notes;

        article.append(notes);
    }


    // ======================================
    // TASK ACTION BUTTONS
    // ======================================

    const actions = document.createElement('div');

    actions.className = 'task-actions';


    // CONTRACT 11: ADD NOTE
    const note = button('Add note', () =>

        run(async () => {

            const text = prompt('Note text:');

            if (text === null) return;

            const res = await api(
                `/api/tasks/${task.task_id}/notes`,
                'POST',
                { text }
            );

            status(
                `Note #${res.note} added.`,
                'success'
            );

            await loadTasks();

        })
    );


    // CONTRACT 12: ADD SUBTASK
    const subtask = button('Add subtask', () =>

        run(async () => {

            const title = prompt('Subtask title:');

            if (title === null) return;

            const res = await api(
                `/api/tasks/${task.task_id}/subtasks`,
                'POST',
                { title }
            );

            status(
                `Subtask created (ID ${res.id}).`,
                'success'
            );

            await loadTasks();

        })
    );


    actions.append(note, subtask);


    // ======================================
    // CONTRACT 13: COMPLETE TASK
    // ======================================

    if (!task.is_complete) {

        const complete = button(
            'Mark complete',
            () => run(async () => {

                await api(
                    `/api/tasks/${task.task_id}/complete`,
                    'POST'
                );

                status(
                    `Task #${task.task_id} completed.`,
                    'success'
                );

                await loadTasks();

            })
        );

        complete.className = 'complete';

        actions.append(complete);
    }

    article.append(actions);


    // ======================================
    // DISPLAY SUBTASKS
    // ======================================

    if (
        Array.isArray(task.subtasks) &&
        task.subtasks.length
    ) {

        const heading = document.createElement('strong');

        heading.textContent = 'Subtasks';

        article.append(heading);

        const list = document.createElement('ul');

        list.className = 'subtask-list';

        for (const item of task.subtasks) {

            const li = document.createElement('li');

            li.textContent =
                `${item.is_complete ? '✓ ' : '○ '}${item.task_name}`;

            list.append(li);
        }

        article.append(list);
    }

    return article;
}


// ==========================================
// BUTTON HELPER
// ==========================================

function button(label, handler) {

    const b = document.createElement('button');

    b.type = 'button';

    b.textContent = label;

    b.addEventListener('click', handler);

    return b;
}
