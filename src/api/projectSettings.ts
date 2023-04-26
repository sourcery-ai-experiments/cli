import {
    IsBoolean,
    IsEnum,
    IsNotEmpty,
    IsOptional,
    IsString,
    IsUrl,
    ValidateNested
} from 'class-validator'
import { Type } from 'class-transformer'

export class EdgeDBSettings {
    @IsBoolean()
    @IsOptional()
    enabled?: boolean;
}
  
export enum PoweredByAlignment {
    CENTER = 'center',
    LEFT = 'left',
    RIGHT = 'right',
    HIDDEN = 'hidden',
  }
  
export class ColorSettings {
    @IsString()
    @IsOptional()
    primary?: string;
  
    @IsString()
    @IsOptional()
    secondary?: string;
}
  
export class OptInSettings {
  @IsString()
  @IsNotEmpty()
  title: string;

  @IsString()
  @IsNotEmpty()
  description: string;

  @IsBoolean()
  enabled: boolean;

  @IsUrl()
  imageURL: string;

  @ValidateNested()
  @Type(() => ColorSettings)
  colors: ColorSettings;

  @IsEnum(PoweredByAlignment)
  poweredByAlignment: PoweredByAlignment;

  @IsOptional()
  @IsBoolean()
  required?: boolean;
}

export class ProjectSettings {
    @ValidateNested()
    edgeDB: EdgeDBSettings;
    
    optIn: Partial<OptInSettings>;
}