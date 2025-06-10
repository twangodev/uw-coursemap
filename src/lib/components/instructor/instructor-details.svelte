<script lang="ts">
  import type { FullInstructorInformation } from "$lib/types/instructor.ts";
  import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card";
  import { Avatar, AvatarFallback } from "$lib/components/ui/avatar";
  import {
    BriefcaseBusiness,
    University,
    GraduationCap,
    Mail,
  } from "@lucide/svelte";

  interface Props {
    instructor: FullInstructorInformation;
  }

  let { instructor }: Props = $props();

  const instructorName = $derived(instructor.name);
</script>

<div class="mt-2 space-y-4 lg:col-span-3">
  <Card>
    <CardHeader class="flex items-center pb-0">
      <Avatar class="h-16 w-16">
        <AvatarFallback class="text-2xl">{instructorName?.at(0)}</AvatarFallback
        >
      </Avatar>
      <CardTitle class="text-2xl font-bold">{instructorName}</CardTitle>
      <CardTitle class="text-muted-foreground text-sm"
        >{instructor.official_name}</CardTitle
      >
    </CardHeader>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">Email</CardTitle>
      <Mail class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    <CardContent>
      <a
        href={`mailto:${instructor.email}`}
        class="text-sm font-medium break-words underline underline-offset-4"
        >{instructor.email}</a
      >
    </CardContent>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">Position</CardTitle>
      <BriefcaseBusiness class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    <CardContent>
      <p class="text-sm break-words">{instructor.position}</p>
    </CardContent>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">Department</CardTitle>
      <University class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    <CardContent>
      <p class="text-sm break-words">{instructor.department}</p>
    </CardContent>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">Credentials</CardTitle>
      <GraduationCap class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    <CardContent>
      <p class="text-sm break-words">{instructor.credentials}</p>
    </CardContent>
  </Card>
</div>
