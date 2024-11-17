<!-- src/components/Footer.svelte -->
<script>
    // Optional: Add any footer logic here if needed
</script>

<footer class="h-16 bg-background py-10 border-t">
    <div class="max-w-screen-xl mx-auto px-4">
        <div class="grid md:grid-cols-3 gap-10">
            <!-- Program Links Section -->
            <div>
                <h3 class="font-semibold text-lg mb-4">Programs</h3>
                <ul class="space-y-2">
                    <li><a href="/programs/major" class="text-sm text-muted-foreground hover:text-foreground transition-colors">Majors</a></li>
                    <li><a href="/programs/certificate" class="text-sm text-muted-foreground hover:text-foreground transition-colors">Certificates</a></li>
                </ul>
            </div>

            <!-- Useful Links Section -->
            <div>
                <h3 class="font-semibold text-lg mb-4">Useful Links</h3>
                <ul class="space-y-2">
                    <li><a href="/calendar" class="text-sm text-muted-foreground hover:text-foreground transition-colors">Academic Calendar</a></li>
                    <li><a href="/contact" class="text-sm text-muted-foreground hover:text-foreground transition-colors">Contact Us</a></li>
                    <li><a href="/faq" class="text-sm text-muted-foreground hover:text-foreground transition-colors">FAQs</a></li>
                </ul>
            </div>

            <!-- Social & Contact Section -->
            <div>
                <h3 class="font-semibold text-lg mb-4">Follow Us</h3>
                <div class="flex space-x-4">
                    <a href="https://facebook.com/uw" class="text-xl text-muted-foreground hover:text-foreground transition-colors">Facebook</a>
                    <a href="https://twitter.com/uw" class="text-xl text-muted-foreground hover:text-foreground transition-colors">Twitter</a>
                </div>
            </div>
        </div>

        <!-- Bottom Section (Legal and Copyright) -->
        <div class="mt-10 border-t border-gray-700 pt-6 text-center">
            <p class="text-sm text-muted-foreground">&copy; 2024 UW Course Map. All rights reserved.</p>
            <div class="mt-2 space-x-4">
                <a href="/privacy-policy" class="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacy Policy</a>
                <a href="/terms-of-service" class="text-sm text-muted-foreground hover:text-foreground transition-colors">Terms of Service</a>
            </div>
        </div>
    </div>
</footer>
