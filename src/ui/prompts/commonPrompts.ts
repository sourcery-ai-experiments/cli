import inquirer from 'inquirer'

export const keyPrompt = async (currentKey?: string): Promise<inquirer.Answers> =>
    inquirer.prompt({
        name: 'key',
        message: `Unique ID${currentKey ? ` (current: ${currentKey})` : ''}`,
        type: 'input',
    })

export const namePrompt = async (currentName?: string): Promise<inquirer.Answers> =>
    inquirer.prompt({
        name: 'name',
        message: `Human readable name${currentName ? ` (current: ${currentName})` : ''}`,
        type: 'input',
    })

export const descriptionPrompt = async (currentDescription?: string): Promise<inquirer.Answers> =>
    inquirer.prompt({
        name: 'description',
        message: `Description for display in the dashboard
            ${currentDescription ? ` (current: ${currentDescription})` : ''}`,
        type: 'input',
    })

export const colorPrompt = async (currentColor?: string): Promise<inquirer.Answers> =>
    inquirer.prompt({
        name: 'color',
        message: `Color for display in dashboard (Hex color code)${currentColor ? ` (current: ${currentColor})` : ''}`,
        type: 'input',
    })