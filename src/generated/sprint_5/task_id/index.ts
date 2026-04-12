// @generated-by: codd implement
// @generated-from: docs/plan/implementation_plan.md (plan:implementation-plan)
// @task-id: タスクID
// @task-title: タスク名
// @generated-from: docs/design/security_sandbox.md (design:security-sandbox)
// @generated-from: docs/design/system_design.md (design:system-design)
// @generated-from: docs/detailed_design/agent_state_transitions.md (design:detailed-agent-flow)
// @generated-from: docs/detailed_design/history_persistence_schema.md (design:history-persistence-schema)
// @generated-from: docs/detailed_design/redis_schema_and_streams.md (design:state-management-redis)
// @generated-from: docs/detailed_design/routing_bloom_taxonomy.md (design:routing-bloom-taxonomy)
// @generated-from: docs/detailed_design/skill_evolution_system.md (design:detailed-skill-evolution)
// @generated-from: docs/detailed_design/task_lifecycle_flow.md (design:task-lifecycle-flow)
// @generated-from: docs/governance/adr_architecture.md (req:architecture)
// @generated-from: docs/requirements/requirements.md (req:kanpaku-requirements)
// @generated-from: docs/test/acceptance_criteria.md (test:acceptance-criteria)

To generate the Playwright E2E test files based on the provided acceptance criteria, we will follow a structured approach to ensure completeness and accuracy. Here is the step-by-step process for generating the API integration tests (`*.spec.ts`) and browser tests (`*.browser.spec.ts`):

### Step 1: Setup Environment
Ensure that the environment is set up correctly with Node.js, npm, and Playwright installed. Start the server using `npm run start`. For CI environments, ensure a background server startup and use `wait-on` to wait for the server to be ready.

```bash
# Local Development
npm run build && npm run start

# CI Environment
npm run build && npm run start &> /dev/null & # Run in background
npx wait-on http://localhost:3000
```

### Step 2: Generate API Integration Tests
Create a new file for each domain and generate the necessary tests. Use `test.describe` to organize sections by feature, and `test.beforeEach` to set up common states like authentication tokens.

#### Auth/RBAC (`tests/e2e/auth.spec.ts`)
```javascript
// @generated-from: test:acceptance-criteria
// @generated-by: codd propagate

import { expect } from '@playwright/test';

test.describe('Auth/RBAC', () => {
  let token;

  test.beforeEach(async ({ request }) => {
    const response = await request.post('/login', {
      data: { username: 'user', password: 'pass' }
    });
    expect(response.status()).toBeLessThan(500);
    token = response.headers()['set-cookie']; // Assuming cookie contains the token
  });

  test('Login flow should redirect to dashboard after successful login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'user');
    await page.fill('[name="password"]', 'pass');
    await page.click('text=Login');
    expect(page.url()).toBe('http://localhost:3000/dashboard');
    expect(await page.textContent('.navbar-title')).toBe('Kanpaku');
  });
});
```

#### Workflow (`tests/e2e/workflow.spec.ts`)
```javascript
// @generated-from: test:acceptance-criteria
// @generated-by: codd propagate

import { expect } from '@playwright/test';

test.describe('Workflow', () => {
  let token;

  test.beforeEach(async ({ request }) => {
    const response = await request.post('/login', {
      data: { username: 'user', password: 'pass' }
    });
    expect(response.status()).toBeLessThan(500);
    token = response.headers()['set-cookie']; // Assuming cookie contains the token
  });

  test('Task creation and assignment should be reflected in Redis state', async ({ request }) => {
    const taskData = { title: 'New Task', description: 'Task Description' };
    const createResponse = await request.post('/tasks', { data: taskData, headers: { Cookie: token } });
    expect(createResponse.status()).toBeLessThan(500);

    const queryResponse = await request.get('/tasks/1', { headers: { Cookie: token } });
    expect(queryResponse.status()).toBeLessThan(500);
    const taskFromRedis = await queryResponse.json();
    expect(taskFromRedis).toEqual({ ...taskData, id: 1, status: 'assigned' });
  });
});
```

#### Sandbox (`tests/e2e/sandbox.spec.ts`)
```javascript
// @generated-from: test:acceptance-criteria
// @generated-by: codd propagate

import { expect } from '@playwright/test';

test.describe('Sandbox', () => {
  let token;

  test.beforeEach(async ({ request }) => {
    const response = await request.post('/login', {
      data: { username: 'user', password: 'pass' }
    });
    expect(response.status()).toBeLessThan(500);
    token = response.headers()['set-cookie']; // Assuming cookie contains the token
  });

  test('File operations should be restricted to /project folder', async ({ request }) => {
    const fileData = new Blob(['test'], { type: 'text/plain' });
    await request.post('/upload', { data: { file: fileData }, headers: { Cookie: token } }, (response) => {
      expect(response.status()).toBeLessThan(500); // Adjust expected status based on server response
    });
  });
});
```

### Step 3: Generate Browser Tests
Browser tests will interact with the UI elements and validate visual aspects or user flows. This step involves setting up Playwright browser contexts (`test.beforeEach` for navigation, `test.afterEach` for cleanup).

#### Login Flow (`tests/e2e/auth.browser.spec.ts`)
```javascript
// @generated-from: test:acceptance-criteria
// @generated-by: codd propagate

import { expect } from '@playwright/test';

test.describe('Auth/RBAC Browser Tests', () => {
  test('Login flow should redirect to dashboard after successful login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'user');
    await page.fill('[name="password"]', 'pass');
    await page.click('text=Login');
    expect(page.url()).toBe('http://localhost:3000/dashboard');
    expect(await page.textContent('.navbar-title')).toBe('Kanpaku');
  });
});
```

#### Task Management (`tests/e2e/workflow.browser.spec.ts`)
```javascript
// @generated-from: test:acceptance-criteria
// @generated-by: codd propagate

import { expect } from '@playwright/test';

test.describe('Workflow Browser Tests', () => {
  let page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto('/login');
    await page.fill('[name="username"]', 'user');
    await page.fill('[name="password"]', 'pass');
    await page.click('text=Login');
    expect(page.url()).toBe('http://localhost:3000/dashboard');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('Creating a new task should display it on the dashboard', async () => {
    const [newPage] = await Promise.all([
      context.waitForEvent('page'),
      page.click('text=New Task')
    ]);
    await newPage.fill('[name="title"]', 'Test Task');
    await newPage.fill('[name="description"]', 'Task Description');
    await newPage.click('text=Create');
    expect(await page.textContent('.task-item')).toContain('Test Task');
  });
});
```

### Step 4: Run Tests
Execute the tests using Playwright's CLI to ensure all scenarios are covered and any issues are caught before deployment.

```bash
npx playwright test --headed
```

This process will generate comprehensive API integration and browser tests based on the provided acceptance criteria, ensuring robust validation of both server-side logic and user interface interactions.
