import { ListQuestion } from 'inquirer'
import { environmentChoices } from './environmentPrompts'

export const environmentPrompt = {
    name: '_environment',
    message: 'Which environment?',
    type: 'list',
    choices: environmentChoices
}

export const sdkKeyTypePrompt: ListQuestion = {
    type: 'list',
    name: 'sdkType',
    message: 'Select the type of SDK key you want to rotate:',
    choices: ['client', 'mobile', 'server'],
}