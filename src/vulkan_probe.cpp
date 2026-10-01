// SPDX-License-Identifier: GPL-3.0-only
#include <vulkan/vulkan.h>
#include <iostream>
#include <vector>

int main()
{
    VkApplicationInfo app{};
    app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app.pApplicationName = "OpenOblivion capability probe";
    app.apiVersion = VK_API_VERSION_1_0;
    VkInstanceCreateInfo info{};
    info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    info.pApplicationInfo = &app;
    VkInstance instance = VK_NULL_HANDLE;
    auto status = vkCreateInstance(&info, nullptr, &instance);
    if (status != VK_SUCCESS)
    {
        std::cerr << "vkCreateInstance failed: " << status << '\n';
        return 1;
    }
    uint32_t count = 0;
    status = vkEnumeratePhysicalDevices(instance, &count, nullptr);
    if (status != VK_SUCCESS || count == 0)
    {
        vkDestroyInstance(instance, nullptr);
        std::cerr << "No Vulkan physical device; enumeration status: " << status << '\n';
        return 1;
    }
    std::vector<VkPhysicalDevice> devices(count);
    status = vkEnumeratePhysicalDevices(instance, &count, devices.data());
    if (status != VK_SUCCESS)
    {
        vkDestroyInstance(instance, nullptr);
        std::cerr << "Vulkan enumeration changed or failed: " << status << '\n';
        return 1;
    }
    for (uint32_t i = 0; i < count; ++i)
    {
        VkPhysicalDeviceProperties props{};
        vkGetPhysicalDeviceProperties(devices[i], &props);
        uint32_t queues = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(devices[i], &queues, nullptr);
        std::vector<VkQueueFamilyProperties> families(queues);
        vkGetPhysicalDeviceQueueFamilyProperties(devices[i], &queues, families.data());
        bool graphics = false;
        for (const auto& family : families)
            graphics |= (family.queueCount > 0 && (family.queueFlags & VK_QUEUE_GRAPHICS_BIT));
        std::cout << "device=" << props.deviceName << " api=" << VK_API_VERSION_MAJOR(props.apiVersion)
                  << '.' << VK_API_VERSION_MINOR(props.apiVersion) << '.' << VK_API_VERSION_PATCH(props.apiVersion)
                  << " type=" << props.deviceType << " graphics_queue=" << graphics << '\n';
    }
    vkDestroyInstance(instance, nullptr);
    return 0;
}
