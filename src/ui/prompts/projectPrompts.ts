import inquirer from 'inquirer'
import { ProjectSettings, OptInSettings, EdgeDBSettings } from '../../api/projectSettings'

export interface CurrentSettings {
  edgeDB: { enabled?: boolean };
  optIn: Partial<OptInSettings>;
}

export const settingsPrompt = async (currentSettings: CurrentSettings): Promise<ProjectSettings | undefined> => {
    const modifySettings = await inquirer.prompt({
        type: 'confirm',
        name: 'modifySettings',
        message: 'Do you want to modify the settings?',
    })

    if (!modifySettings.modifySettings) {
        return undefined
    }

    const chooseSettings = await inquirer.prompt({
        type: 'checkbox',
        name: 'selectedSettings',
        message: 'Select the settings you want to modify:',
        choices: ['edgeDB', 'optIn'],
    })

    let edgeDBEnabled: EdgeDBSettings = { enabled: false }
    if (chooseSettings.selectedSettings.includes('edgeDB')) {
        const { enabled = false } = await inquirer.prompt({
            type: 'confirm',
            name: 'enabled',
            message: `Enable edgeDB? (current: ${currentSettings.edgeDB.enabled || false})`,
        })
        edgeDBEnabled = { enabled }
    }

    let optIn: Partial<OptInSettings> = {}
    if (chooseSettings.selectedSettings.includes('optIn')) {
        optIn = await inquirer.prompt([
            {
                type: 'input',
                name: 'title',
                message: 'Opt-in title:',
            },
            {
                type: 'input',
                name: 'description',
                message: 'Opt-in description:',
            },
            {
                type: 'confirm',
                name: 'enabled',
                message: 'Enable opt-in?',
            },
            {
                type: 'input',
                name: 'imageURL',
                message: 'Image URL:',
            },
            {
                type: 'confirm',
                name: 'modifyAlignment',
                message: 'Do you want to modify the poweredByAlignment setting?',
                when: (answers) => answers.enabled === true,
            },
            {
                type: 'list',
                name: 'poweredByAlignment',
                message: 'Choose poweredByAlignment:',
                choices: ['left', 'center', 'right', 'hidden'],
                when: (answers) => answers.modifyAlignment === true,
            },
        ])

        const colors = await inquirer.prompt([
            {
                type: 'input',
                name: 'primary',
                message: 'Primary color (Hex color code):',
            },
            {
                type: 'input',
                name: 'secondary',
                message: 'Secondary color (Hex color code):',
            },
        ])

        optIn = { ...optIn, colors }
    }

    return {
        edgeDB: edgeDBEnabled,
        optIn,
    }
}
