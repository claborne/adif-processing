# Created  12/2/2025
# copyright 2025, Christian Claborne, The Ham Ninja, N1CLC
# licensed under the GNU General Public License (GPL), specifically version 2 (GPLv2)
# I needed an app to modify ADIF files so I used claude.ai for a draft 
# then modified to fit my needs as well as fixing a bug created by claude.ai
# My initial needs could be met in just a few lines of code but this is more flexible

# USAGE: edit-adif <input_file> <output_file> <value> [<filed_name> | -f]
# If no arguments are passed, it outputs help on usage and prompts you for all values
# If output file = "-f" this enables full override and assumes defaults of
#         <input_file> foo.adi SOTA OTHER
# Full override skips the confirmation step at the end and executes unless input_file = output_file
# Output file can be left off and it proposes a default
# It expects to see some sort of "activity" for the value but allows override at runtime
# My default field name is "OTHER" and you won't be prompted if you use -f


# commented out user prompt for field to be updated

# Used to add data for the ADIF <other> field for importing to AC Log
# This capability was 85 lines but it couldn't edit files that had the field, not did it allow you to set the field name
# This version is much more useful
############################
# v1.0
#   initial creation
# v1.01
#   Fixed an issue where reading assumed uft-8 files would crash
# V1.02
#   If you pass "-f" as the output file name at the end,
#   sets default values
#   This version does not allow the input and output files to be the same

import re
import sys


def parse_adif_record(record):
    """
    Parse an ADIF record and extract field-value pairs.
    Returns a dictionary of fields and the raw record.
    """
    fields = {}
    # Pattern to match ADIF fields: <FIELD:length>value or <FIELD:length:type>value
    pattern = r'<(\w+):(\d+)(?::(\w))?>([^<]*)'

    for match in re.finditer(pattern, record):
        field_name = match.group(1).upper()
        length = int(match.group(2))
        value = match.group(4)[:length]
        fields[field_name] = value

    return fields


def add_field_to_record(record, field_name, field_value):
    """
    Add or update a field in an ADIF record before the <EOR> marker.
    If the field already exists, it will be replaced with the new value.
    """
    # Create the new field in ADIF format
    new_field = f"<{field_name}:{len(field_value)}>{field_value}"

    # Check if the field already exists
    # Pattern to match the specific field: <FIELDNAME:length>value or <FIELDNAME:length:type>value
    field_pattern = rf'<{field_name}:\d+(?::\w)?>[^<]*'

    if re.search(field_pattern, record, re.IGNORECASE):
        # Field exists, replace it
        updated_record = re.sub(field_pattern, new_field, record, flags=re.IGNORECASE)

        # quigmod put the EOR back
        # This is a hack because I don't know why the EOR is getting stripped off!!!!!!!!!
        updated_record = updated_record + " <EOR>"
    else:
        # Field doesn't exist, add it before <EOR>
        if '<EOR>' in record.upper():
            # Insert before <EOR>
            eor_pos = record.upper().rfind('<EOR>')
            updated_record = record[:eor_pos] + new_field + ' ' + record[eor_pos:]
        else:
            # If no <EOR>, just append the field
            updated_record = record.strip() + ' ' + new_field + ' <EOR>\n'

    return updated_record


def update_adif_file(input_file, output_file, field_name, field_value):
    """
    Read an ADIF file, add a field to each record, and write to output file.
    """
    try:
        #with open(input_file, 'r', encoding='utf-8') as f:  #fixes a bug where a dump file contains something it doesn't like.
        with open(input_file, 'r') as f:
            content = f.read()

        # Split content into header and records
        # ADIF header ends with <EOH>
        if '<EOH>' in content.upper():
            header_end = content.upper().find('<EOH>') + 5
            header = content[:header_end]
            records_section = content[header_end:]
        else:
            header = ""
            records_section = content

        # Split records by <EOR>
        records = re.split(r'<EOR>', records_section, flags=re.IGNORECASE)

        updated_records = []
        record_count = 0
        updated_count = 0
        added_count = 0

        for record in records:
            record = record.strip()
            if record:  # Skip empty records
                # Check if field already exists
                field_pattern = rf'<{field_name}:\d+(?::\w)?>[^<]*'
                field_exists = bool(re.search(field_pattern, record, re.IGNORECASE))

                updated_record = add_field_to_record(record, field_name, field_value)
                updated_records.append(updated_record)
                record_count += 1

                if field_exists:
                    updated_count += 1
                else:
                    added_count += 1

        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            if header:
                f.write(header + '\n')
            f.write('\n'.join(updated_records))

        print(f"✅ Successfully processed {record_count} records")
        print(f"  - Added {field_name} to {added_count} records")
        print(f"  - Updated {field_name} in {updated_count} records")
        print(f"✅ Output written to: {output_file}")
        return True

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

#############################################################
#####                     Entry Point                   #####
#############################################################
def main():
    """Main function to run the ADIF updater."""
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = ""

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = ""
    if output_file.upper() == '-F':
        user_override = 'Y'
    else:
        user_override = 'N'

    if len(sys.argv) > 3:
        field_value = sys.argv[3].upper()
    else:
        field_value = ""

    if len(sys.argv) > 4:
        field_name = sys.argv[4].upper()
    else:
        field_name = ""  # initialize the field

    if user_override == 'Y':
        output_file = 'foo.adi'
        field_value = 'SOTA'
        field_name = 'OTHER'
        
        print("=== ADIF Field Updater ===\n")

    # Get input file
    if input_file == output_file:  #input can't equal output
        input_file = ""
        print(f"\nERROR!: INPUT FILE CAN NOT EQUAL OUTPUT FILE NAME\n")

    if not input_file:
        print(f"\nUSAGE: {sys.argv[0]} <input_file> <output_file> <activity> <output file>")
        input_file = input("\nEnter INPUT ADIF file path or Q to QUIT: ").strip()

        if input_file.strip().upper() == "Q":
            print("\nQuitting.")
            sys.exit()  # user wants to exit

    # Get output file

    if not output_file:
        default_output = input_file.replace('.adi', '_updated.adi').replace('.adif', '_updated.adif')
        if not default_output.endswith(('.adi', '.adif')):
            default_output += '_updated.adi'

        output_file = input(f"Enter OUTPUT file path (default: {default_output}): ").strip()
        if not output_file:
            output_file = default_output


##########################################################
############## FIELD VALUE PROCESSING         ############
##########################################################

    passed = 0
    while passed == 0:
        if not field_value:  # user didn't supply activity on the command line so prompt for it
            # Prompt the user for replacement text
            field_value = input(
                "\nEnter text for other field (ex SOTA|POTA|CHASE|HUNT|FIELD|CONTEST) [q to quit]: ").strip().upper()

            ###### quigremovefield_value = user_input.strip().upper() #go ahead and stash the value
        #else:
        #    user_input = field_value.strip().upper()

        if field_value.strip().upper() == "Q":
            print("\nQuitting.")
            sys.exit()  # user wants to exit

        # Check user input
        if field_value not in ["SOTA", "POTA", "SPOTA", "CHASE", "HUNT", "FIELD", "CONTEST"]:
            # print("\nYou must enter one of the following: SOTA, POTA, SPOTA, CHASE, HUNT, FIELD, CONTEST.")
            print("\nI expected one of the following: SOTA, POTA, SPOTA, CHASE, HUNT, FIELD, CONTEST.")

            user_override = "N"
            user_override = input("Do you want to OVERRIDE?: (y/n): ").strip().upper()
            if user_override.strip().upper() == "Q":
                print("\nQuitting.")
                sys.exit()  # user wants to exit
                
            if user_override.strip().upper() == "Y":
                passed = 1
            else:
                passed = 0
                field_value = ""  # null the value in case junk was set
        else:
            # everything looks good
            passed = 1

    ##########################################################

    if field_name != '-F':   # we don't want to force it
        #print(f"The field name is currently set to {field_name}")
        # Get field name to add or update  (default to "OTHER")
        if not field_name:  # nothing was passed on the command line
            field_name = input("Enter field name to add or update (default: OTHER, q to Quit): ").strip().upper()
            
            if field_name == "Q":
                print("\nQuitting.")
                sys.exit()  # user wants to exit

            if not field_name:  # user entered nothing
                field_name = "OTHER"
    else:
        field_name = "OTHER"

    # Confirm before proceeding
    print(f"\nWill add/update <{field_name}:{len(field_value)}>{field_value} to all records")
    print(f"(Existing {field_name} fields will be updated with the new value)")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")

    if user_override == 'N':
        confirm = input("\nProceed? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled")
            return
    # Process the file
    print("\nProcessing...")
    update_adif_file(input_file, output_file, field_name, field_value)


if __name__ == "__main__":
    main()