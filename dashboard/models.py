from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)


class Organization(models.Model):

    PROVIDER_CHOICES = [
        ('P', 'Peplink'),
        ('M', 'Meraki'),
    ]
    name = models.CharField(max_length=255)
    org_id = models.CharField("Organization ID",  max_length=100)
    org_type = models.CharField("Organization Type", max_length=255, choices=PROVIDER_CHOICES, default='P')
    org_url = models.URLField("Organization URL", max_length=255, null=True, blank=True)
    api_enabled = models.BooleanField("Enable API", default=True)
    class Meta:
        unique_together = ('org_id', 'org_type')

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=255)

    # peplink_org = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    # meraki_org = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)

    contact_person = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.EmailField(max_length=255, null=True, blank=True)
    primary_contact_no = models.CharField(max_length=255, null=True, blank=True)
    secondary_contact_no = models.CharField(max_length=255, null=True, blank=True)
    organization = models.ManyToManyField(Organization, through='CustomerOrganization')
    # these are users who have access to Customer data
    users = models.ManyToManyField("auth.User", through="CustomerUsers")


    class Meta:
        verbose_name = "Customer Information"
        verbose_name_plural = "Customer Information"

    @property
    def initials(self):
        first_3_words = self.name.split(" ")[:3]
        initials = "".join([w[0] for w in first_3_words]).upper()
        return initials
    def __str__(self):
        return self.name


class CustomerOrganization(models.Model):
    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    organization = models.ForeignKey("dashboard.Organization", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Customer's Organizations"

    def __str__(self):
        return self.customer.name

class CustomerUsers(models.Model):
    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Portal User"
        verbose_name_plural = "Customer's Portal Users"


    def __str__(self):
        name = ""
        # get the first name and last name for the user if it exists
        # if not just return the username

        if self.user:
            name = self.user.username
            if  self.user.first_name != "" and self.user.last_name != "":
                name = self.user.first_name + " " + self.user.last_name

        return name
