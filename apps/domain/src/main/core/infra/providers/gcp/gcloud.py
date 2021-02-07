import subprocess


class GCloud:
    def projects_list(self):
        proc = subprocess.Popen(
            'gcloud projects list --format="value(projectId)"',
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        projects = proc.stdout.read()
        return projects.split()

    def regions_list(self):
        proc = subprocess.Popen(
            'gcloud compute regions list --format="value(NAME)"',
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        regions = proc.stdout.read()
        return regions.split()

    def zones_list(self, region):
        proc = subprocess.Popen(
            f'gcloud compute zones list --filter="REGION:( {region} )" --format="value(NAME)"',
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        zones = proc.stdout.read()
        return zones.split()

    def machines_type(self, zone):
        proc = subprocess.Popen(
            f'gcloud compute machine-types list --filter="ZONE:( {zone} )" --format="value(NAME)"',
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        machines = proc.stdout.read()
        return machines.split()

    def images_type(self):
        proc = subprocess.Popen(
            f'gcloud compute images list --format="value(NAME,PROJECT,FAMILY)"',
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        images = proc.stdout.read().split()
        images = {
            images[i]: (images[i + 1], images[i + 2]) for i in range(0, len(images), 3)
        }
        return images
