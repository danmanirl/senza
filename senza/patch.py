
import boto3
import datetime

LAUNCH_CONFIGURATION_PROPERTIES = set([
    'AssociatePublicIpAddress',
    'BlockDeviceMappings',
    'ClassicLinkVPCId',
    'ClassicLinkVPCSecurityGroups',
    'EbsOptimized',
    'IamInstanceProfile',
    'ImageId',
    'InstanceId',
    'InstanceMonitoring',
    'InstanceType',
    'KernelId',
    'KeyName',
    'LaunchConfigurationName',
    'PlacementTenancy',
    'RamdiskId',
    'SecurityGroups',
    'SpotPrice',
    'UserData',
])


def patch_auto_scaling_group(group, region, properties):
    asg = boto3.client('autoscaling', region)
    result = asg.describe_launch_configurations(LaunchConfigurationNames=[group['LaunchConfigurationName']])
    lcs = result['LaunchConfigurations']
    changed = False
    for lc in lcs:
        lc_props = {k: lc[k] for k in properties}
        if properties != lc_props:
            # create new launch configuration with specified properties
            kwargs = {}
            for key in LAUNCH_CONFIGURATION_PROPERTIES:
                # NOTE: we only take non-empty values (otherwise the parameter validation will complain :-( )
                val = lc.get(key)
                if val is not None and val != '':
                    kwargs[key] = lc[key]
            now = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S')
            kwargs['LaunchConfigurationName'] = '{}-{}'.format(kwargs['LaunchConfigurationName'][:64], now)
            kwargs.update(**properties)
            asg.create_launch_configuration(**kwargs)
            asg.update_auto_scaling_group(AutoScalingGroupName=group['AutoScalingGroupName'],
                                          LaunchConfigurationName=kwargs['LaunchConfigurationName'])
            changed = True
    return changed