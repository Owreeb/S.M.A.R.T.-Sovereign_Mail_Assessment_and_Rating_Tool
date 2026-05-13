# Development Guidelines

**Project:**
**Version:** 1.0
**Date:** 26.03.2026

## 1. Branching & Workflow

### Branch Types:
|Branch|Purpose|
|--|--|
|`main`|Production-ready code|
|`feature/<name>`|New feature|
|`bugfix/<name>`|Bug fixes|
|`chore/<name>`|Refactoring, dependency updates, CI/CD changes|

<br/>

### Workflow Rules:
 - Always branch off from `main`
 - Keep branches small and focused
 - No direct commits to `main`

<br/>

## 2. Pull Request Guidelines

### PR Naming Convention:
    <type>: <short description>
 
#### Types:
|Type|Purpose|
|--|--|
|`feat:`|New feature|
|`fix:`|Bug fixes|
|`refactor:`|Code improvement/refactoring|
|`chore:`|Maintenance such as dependency updates|
<br/>

### PR Template & Checklist:
    ## What
    Short description of the change
    
    ## Notes
    Optional additional information
	Implementer:
		- [] I have verified that my implementation covers all acceptance criteria of the Jira ticket
		- [] I have implemented/extended a unit/E2E test for my new feature
	Reviewer: 
		- [] I have verified that the implementation covers all acceptance criteria of the Jira ticket
		- [] I have reviewed/extended a unit/E2E test for the new feature

<br/>

### Definition of Done:
 - [x] Code compiles successfully
 - [x] All automated tests pass
 - [x] At least one reviewer has approved
 - [x] All comments are resolved
 - [x] Documentation has been updated if necessary

 <br/>
 
## 3. Guidelines for Code Reviewers

### Reviewer Responsibilities:
 - Verify correctness
 - Ensure readability and maintainability
 - Confirm that the implementation follows project patterns

<br/>

### Focus Areas:
 - Correctness --> Does it work?
 - Readability --> Easy to understand?
 - Maintainability --> Easy to extend/modify?
 - Performance --> Efficient?

<br/>

### Feedback Style:
 - Be constructive and specific
 - Suggest rather than command

<br/>

### Approval Rules:
- At least 1 approval required
- PR cannot be merged without approval or with unresolved comments

<br/>

## 4. Coding Standards & Best Practices

### Naming & Style:
|Type|Style|Example|
|--|--|--|
|Classes / Types / Interfaces|PascalCase|`ExampleName`|
|Functions / Methods|camelCase|`exampleName()`|
|Variables|camelCase|`exampleName`|
|Constants|Screaming Snake Case|`EXAMPLE_NAME`|

<br/>

### Architecture & Structure:
- Follow existing project patterns
- Reuse existing logic where possible

<br/>

### Error Handling & Logging:
- Handle errors explicitly – avoid silent failures
- Use structured logging consistently

<br/>

### Testing:
- Write unit tests for all business logic
- Ensure coverage of edge cases
- Mock external dependencies in tests
- Code coverage % still to be determined

<br/>

### General Best Practices:
- Store secrets in environment variables and never commit them
- Avoid repetition (DRY)
- Remove debug statements before merging
- Add comments for complex or confusing logic

<br/>

## 5. CI/CD Pipeline Guidelines

### Pipeline Triggers:
- Every pull request
- Every push to `main`

<br/>

### Pipeline Stages:
- Build
- Run tests
- Sonar?
- *Remainder still to be determined*

<br/>

### Pipeline Rules:
- Pull requests cannot be merged if the pipeline fails
- If the pipeline is broken, fixing it has the highest priority
