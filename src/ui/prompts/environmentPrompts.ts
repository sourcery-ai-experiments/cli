import {
    Environment,
    environmentTypes,
    fetchEnvironments,
    sdkTypes
} from '../../api/environments'

type EnvironmentChoice = {
    name: string,
    value: string
}

export const environmentChoices = async (token: string, projectKey: string): Promise<EnvironmentChoice[]> => {
    const environments = await fetchEnvironments(token, projectKey)
    const choices = environments.map((environment: Environment) => {
        return {
            name: environment.name || environment.key,
            value: environment.key // Use the environment key as the value
        }
    })
    return choices
}
export const environmentPrompt = {
    name: '_environment',
    message: 'Which environment?',
    type: 'list',
    choices: environmentChoices
}

export const environmentTypePrompt = {
    name: 'type',
    message: 'The type of environment',
    type: 'list',
    choices: environmentTypes
}

export const sdkKeyTypePrompt = {
    name: 'sdkType',
    message: 'Which SDK?',
    type: 'list',
    choices: sdkTypes.concat(['all'])
}