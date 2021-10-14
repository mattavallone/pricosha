# PriCoSha
## Team Members
* Matthew Avallone
* Beamlak Hailemariam
* Allie Haber

## Description 
PriCoSha is a platform where users can share content items to the public, as well as privately to a specific FriendGroup.
FriendGroups are owned by a single user, though a user can own multiple FriendGroups. There can be no FriendGroups with the same name and owner. The owner can add/remove other users from his/her own group. A FriendGroup can have many users that Belong to it, and users can belong to multiple FriendGroups.
Users have access to a post if it was made public, or it was shared privately with one of their FriendGroups. Users can view posts, tag other users, rate posts, and see more info about the post once they have access.
Users can tag another user in a post as long as the new user has access to that post as well. When a user is tagged, the tag appears in their “Tags Pending” section. The tagged user then has the option to accept the tag, decline the tag, or leave the tag as pending. When a user accepts a tag, it gets added to their “Approved Tags”, and if they decline it, the tag gets deleted. Once a user approves the tag, they will appear under “Tagged People” for that post.
There were four extra features implemented:
* A location attribute was added to contentItem, where users can see Persons who have posted content in similar areas. 
* Users can add comments about content that is visible to them. It gets stored in a “comments” table with an ID as primary key for the comment, the person who is commenting, the content item the comment refers to, the text for the comment itself and a bool for whether or not the comment is public. 
* A user can unfriend another person. This means the unfriended person is removed from all FriendGroups that the user is in and tags on all content items shared with those FriendGroups. 
* Users can create their own FriendGroups. They can specify a group name and a description, as well as add Persons to it.

## Group Member Contributions


* Matthew Avallone
   * View Public Content
   * Login/Registration
   * Post a content item
   * Location Tracking
   * Adding comments
* Beamlak Hailemariam
   * View share content items and info on them
   * Add friends
   * Unfriend
* Allie Haber
   * Manage tags
   * Tag a content item
   * Create a group
