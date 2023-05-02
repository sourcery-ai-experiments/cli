import {
    Environment,
    environmentTypes,
    fetchEnvironments,
    sdkTypes,
} from '../../api/environments'

type EnvironmentChoice = {
    name: string
    value: string
}

const allEnvironments: EnvironmentChoice[] = [{
    name: 'All',
    value: 'all',
}]

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const environmentIdChoices = async (
    input: Record<string, any>,
): Promise<EnvironmentChoice[]> => {
    const environments = await fetchEnvironments(input.token, input.projectKey)
    const choices = environments.map((environment: Environment) => {
        return {
            name: environment.name || environment.key,
            value: environment._id,
        }
    })
    return choices
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const environmentKeyChoices = async (
    input: Record<string, any>,
): Promise<EnvironmentChoice[]> => {
    const environments = await fetchEnvironments(input.token, input.projectKey)
    const choices = environments.map((environment: Environment) => {
        return {
            name: environment.name || environment.key,
            value: environment.key,
        }
    })
    return choices
}

export const environmentKeyAllChoices = async (
    input: Record<string, any>,
): Promise<EnvironmentChoice[]> => {
    const environmentKeyAllChoices = await environmentKeyChoices(input)
    return allEnvironments.concat(environmentKeyAllChoices)
}

export const environmentIdPrompt = {
    name: '_environment',
    message: 'Which environment?',
    type: 'list',
    choices: environmentIdChoices,
}

export const environmentKeyPrompt = {
    name: 'environment',
    message: 'Which environment?',
    type: 'list',
    choices: environmentKeyChoices,
}

export const environmentKeyAllPrompt = {
    name: 'environment',
    message: 'Which environment?',
    type: 'list',
    choices: environmentKeyAllChoices,
}

export const environmentTypePrompt = {
    name: 'type',
    message: 'The type of environment',
    type: 'list',
    choices: environmentTypes,
}

export const sdkKeyTypePrompt = {
    name: 'sdkType',
    message: 'Which SDK?',
    type: 'list',
    choices: sdkTypes.concat(['all']),
}
