import inquirer from 'inquirer'
import { ProjectSettings, OptInSettings, EdgeDBSettings, PoweredByAlignment } from '../../api/projectSettings'

export interface CurrentSettings {
  edgeDB: { enabled?: boolean };
  optIn: Partial<OptInSettings>;
}

export const settingsPrompt = async (currentSettings: CurrentSettings)
    : Promise<Partial<ProjectSettings> | undefined> => {
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

    const optIn: Partial<OptInSettings> = {}
    if (chooseSettings.selectedSettings.includes('optIn')) {
        const optInSettingsToUpdate = await inquirer.prompt({
            type: 'checkbox',
            name: 'optInSettings',
            message: 'Select the opt-in settings you want to modify:',
            choices: [
                { name: 'title', value: 'title' },
                { name: 'description', value: 'description' },
                { name: 'enabled', value: 'enabled' },
                { name: 'imageURL', value: 'imageURL' },
                { name: 'poweredByAlignment', value: 'poweredByAlignment' },
            ],
        })

        for (const setting of optInSettingsToUpdate.optInSettings) {
            const currentValue = currentSettings.optIn[setting as keyof OptInSettings] || ''
          
            let prompt: inquirer.Question<inquirer.Answers>
          
            if (setting === 'enabled' || setting === 'poweredByAlignment') {
                prompt = {
                    type: 'confirm',
                    name: setting,
                    message: `${setting.charAt(0).toUpperCase()}${setting.slice(1)} (current: ${currentValue}):`,
                } as inquirer.ConfirmQuestion<inquirer.Answers>
            } else {
                prompt = {
                    type: 'input',
                    name: setting,
                    message: `${setting.charAt(0).toUpperCase()}${setting.slice(1)} (current: ${currentValue}):`,
                } as inquirer.InputQuestion<inquirer.Answers>
            }
          
            if (setting === 'poweredByAlignment') {
                (prompt as inquirer.ListQuestion<inquirer.Answers>).type = 'list';
                (prompt as inquirer.ListQuestion<inquirer.Answers>).choices = Object.values(PoweredByAlignment)
            }
          
            const answer = await inquirer.prompt([prompt])
            optIn[setting as keyof OptInSettings] = answer[setting]
        }
    }
}
